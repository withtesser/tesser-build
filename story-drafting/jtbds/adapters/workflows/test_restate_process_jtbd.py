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
import pytest
import restate
import restate.client as restate_client

import jtbds.adapters.activities as activities
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


class TestRestateProcessJtbd:

    async def test_process_jtbd_calls_initialize_jtbd_through_the_engine_and_answers_with_what_it_recorded(self) -> None:
        workflow_key = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        job_to_be_done_actions_service = restate.Service(f"JobToBeDoneActions{suffix}")
        job_to_be_done_orchestrator_workflow = restate.Workflow(f"JobToBeDoneOrchestrator{suffix}")
        parent_target = f"JobToBeDoneOrchestrator{suffix}/" + workflow_key + "/process_jtbd"
        fake_job_to_be_done_application_client = FakeJobToBeDoneApplicationClient()
        restate_process_jtbd = workflows.RestateProcessJtbd(
            job_to_be_done_orchestrator_workflow,
            activities.RestateInitializeJtbd(job_to_be_done_actions_service, fake_job_to_be_done_application_client),
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

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                with pytest.raises(restate.HttpError) as foreign:
                    await restate_client.Client(async_client).workflow_call(
                        restate_process_jtbd.handler, key="other-" + workflow_key, arg=relays.ProcessJtbdRequest(jtbd_id=workflow_key, description="design new feature", status="drafting")
                    )
                process_jtbd_response = await restate_client.Client(async_client).workflow_call(
                    restate_process_jtbd.handler, key=workflow_key, arg=relays.ProcessJtbdRequest(jtbd_id=workflow_key, description="design new feature", status="drafting")
                )
            invoked = await admin.post(
                "/query",
                headers={"accept": "application/json"},
                json={
                    "query": "SELECT target, completion_result FROM sys_invocation "
                    "WHERE invoked_by_target = '" + parent_target + "'"
                },
            )

            assert foreign.value.status_code == 400
            assert process_jtbd_response == relays.ProcessJtbdResponse(jtbd_id=workflow_key)
            assert [recorded.jtbd_id for recorded in fake_job_to_be_done_application_client.recorded] == [workflow_key]
            assert [(row["target"], row["completion_result"]) for row in invoked.json()["rows"]] == [
                (f"JobToBeDoneActions{suffix}/initialize_jtbd", "success")
            ]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
