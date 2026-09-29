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

import story_drafting.adapters.activities as activities
import story_drafting.adapters.workflows as workflows
import story_drafting.application.client as client
import story_drafting.application.relays as relays


@ts.fake
class FakeJtbdApplicationClient(client.JtbdApplicationClient):

    def __init__(self) -> None:
        self.recorded: list[relays.BeginDraftingRequest] = []

    async def begin_drafting(self, begin_drafting_request: relays.BeginDraftingRequest) -> relays.BeginDraftingResponse:
        self.recorded.append(begin_drafting_request)
        return relays.BeginDraftingResponse(jtbd_id=begin_drafting_request.jtbd_id)


class TestRestateBeginDraftProcess:

    async def test_begin_draft_process_calls_begin_drafting_through_the_engine_and_answers_with_what_it_recorded(self) -> None:
        workflow_key = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        jtbd_actions_service = restate.Service(f"JtbdActions{suffix}")
        jtbd_orchestrator_workflow = restate.Workflow(f"JtbdOrchestrator{suffix}")
        parent_target = f"JtbdOrchestrator{suffix}/" + workflow_key + "/begin_draft_process"
        fake_jtbd_application_client = FakeJtbdApplicationClient()
        restate_begin_draft_process = workflows.RestateBeginDraftProcess(
            jtbd_orchestrator_workflow,
            activities.RestateBeginDrafting(jtbd_actions_service, fake_jtbd_application_client),
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

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                with pytest.raises(restate.HttpError) as foreign:
                    await restate_client.Client(async_client).workflow_call(
                        restate_begin_draft_process.handler, key="other-" + workflow_key, arg=relays.BeginDraftProcessRequest(jtbd_id=workflow_key, status="drafting")
                    )
                begin_draft_process_response = await restate_client.Client(async_client).workflow_call(
                    restate_begin_draft_process.handler, key=workflow_key, arg=relays.BeginDraftProcessRequest(jtbd_id=workflow_key, status="drafting")
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
            assert begin_draft_process_response == relays.BeginDraftProcessResponse(jtbd_id=workflow_key)
            assert [recorded.jtbd_id for recorded in fake_jtbd_application_client.recorded] == [workflow_key]
            assert [(row["target"], row["completion_result"]) for row in invoked.json()["rows"]] == [
                (f"JtbdActions{suffix}/begin_drafting", "success")
            ]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
