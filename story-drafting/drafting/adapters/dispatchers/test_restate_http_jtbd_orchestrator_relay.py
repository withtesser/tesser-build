from __future__ import annotations

import asyncio
import os
import socket
import typing
import uuid

import tesser.testing as ts
import httpx
import hypercorn.asyncio as hypercorn_asyncio
import hypercorn.config as hypercorn_config
import hypercorn.typing as hypercorn_typing
import restate

import drafting.adapters.activities as activities
import drafting.adapters.dispatchers as dispatchers
import drafting.adapters.workflows as workflows
import drafting.application.client as client
import drafting.application.relays as relays


@ts.fake
class FakeJtbdApplicationClient(client.JtbdApplicationClient):

    def __init__(self) -> None:
        self.recorded: list[relays.RecordJtbdRequest] = []

    async def record_jtbd(self, record_jtbd_request: relays.RecordJtbdRequest) -> relays.RecordJtbdResponse:
        self.recorded.append(record_jtbd_request)
        return relays.RecordJtbdResponse(jtbd_id=record_jtbd_request.jtbd_id)


class TestRestateHttpJtbdOrchestratorRelay:

    async def test_work_through_jtbd_runs_the_workflow_the_engine_keys_by_the_jtbd_id(self) -> None:
        workflow_key = "../admin?x=1#f-" + str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        jtbd_actions_service = restate.Service(f"JtbdActions{suffix}")
        jtbd_orchestrator_workflow = restate.Workflow(f"JtbdOrchestrator{suffix}")
        restate_work_through_jtbd = workflows.RestateWorkThroughJtbd(
            jtbd_orchestrator_workflow,
            activities.RestateRecordJtbd(jtbd_actions_service, FakeJtbdApplicationClient()),
        )
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([jtbd_actions_service, jtbd_orchestrator_workflow])),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        admin = httpx.AsyncClient(base_url=os.environ["RESTATE_ADMIN"], timeout=10.0)
        registered = httpx.Response(503)
        try:
            for _ in range(50):
                registered = await admin.post(
                    "/deployments",
                    json={"uri": f"http://{os.environ['RESTATE_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            work_through_jtbd_response = await dispatchers.RestateHttpJtbdOrchestratorRelay(
                os.environ["RESTATE_INGRESS"], restate_work_through_jtbd
            ).run_work_through_jtbd(relays.WorkThroughJtbdRequest(jtbd_id=workflow_key, situation="I am working through a multi-step piece of work with an agent", motivation="the steps and my checkpoints fixed in advance", outcome="I can step away and resume where we were"))
            invoked = await admin.post(
                "/query",
                headers={"accept": "application/json"},
                json={
                    "query": "SELECT target_service_key, invoked_by, completion_result FROM sys_invocation "
                    f"WHERE target_service_name = 'JtbdOrchestrator{suffix}'"
                },
            )

            assert work_through_jtbd_response == relays.WorkThroughJtbdResponse(jtbd_id=workflow_key)
            assert [
                (row["target_service_key"], row["invoked_by"], row["completion_result"]) for row in invoked.json()["rows"]
            ] == [(workflow_key, "ingress", "success")]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
