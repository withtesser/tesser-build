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

import jtbds.adapters.activities as activities
import jtbds.adapters.dispatchers as dispatchers
import jtbds.adapters.workflows as workflows
import jtbds.application.client as client
import jtbds.application.relays as relays


@ts.fake
class FakeJobToBeDoneApplicationClient(client.JobToBeDoneApplicationClient):

    def __init__(self) -> None:
        self.recorded: list[relays.InitializeJtbdRequest] = []

    async def initialize_jtbd(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> relays.InitializeJtbdResponse:
        self.recorded.append(initialize_jtbd_request)
        return relays.InitializeJtbdResponse(jtbd_id=initialize_jtbd_request.jtbd_id)


class TestRestateHttpJobToBeDoneOrchestratorRelay:

    async def test_process_jtbd_runs_the_workflow_the_engine_keys_by_the_jtbd_id(self) -> None:
        workflow_key = "../admin?x=1#f-" + str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        job_to_be_done_actions_service = restate.Service(f"JobToBeDoneActions{suffix}")
        job_to_be_done_orchestrator_workflow = restate.Workflow(f"JobToBeDoneOrchestrator{suffix}")
        restate_process_jtbd = workflows.RestateProcessJtbd(
            job_to_be_done_orchestrator_workflow,
            activities.RestateInitializeJtbd(job_to_be_done_actions_service, FakeJobToBeDoneApplicationClient()),
        )
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([job_to_be_done_actions_service, job_to_be_done_orchestrator_workflow])),
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

            process_jtbd_response = await dispatchers.RestateHttpJobToBeDoneOrchestratorRelay(
                os.environ["RESTATE_INGRESS"], restate_process_jtbd
            ).run_process_jtbd(relays.ProcessJtbdRequest(jtbd_id=workflow_key, description="design new feature", status="drafting"))
            invoked = await admin.post(
                "/query",
                headers={"accept": "application/json"},
                json={
                    "query": "SELECT target_service_key, invoked_by, completion_result FROM sys_invocation "
                    f"WHERE target_service_name = 'JobToBeDoneOrchestrator{suffix}'"
                },
            )

            assert process_jtbd_response == relays.ProcessJtbdResponse(jtbd_id=workflow_key)
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
