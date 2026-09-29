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

import jtbd.adapters.activities as activities
import jtbd.adapters.workflows as workflows
import jtbd.application.client as client
import jtbd.application.relays as relays


@ts.fake
class FakeJtbdApplicationClient(client.JtbdApplicationClient):

    def __init__(self) -> None:
        self.recorded: list[relays.MarkJtbdDraftingRequest] = []

    async def mark_jtbd_drafting(self, mark_jtbd_drafting_request: relays.MarkJtbdDraftingRequest) -> relays.MarkJtbdDraftingResponse:
        self.recorded.append(mark_jtbd_drafting_request)
        return relays.MarkJtbdDraftingResponse(jtbd_id=mark_jtbd_drafting_request.jtbd_id)


class TestRestateDraftForJtbd:

    async def test_draft_for_jtbd_calls_mark_jtbd_drafting_through_the_engine_and_answers_with_what_it_recorded(self) -> None:
        workflow_key = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        jtbd_actions_service = restate.Service(f"JtbdActions{suffix}")
        jtbd_orchestrator_workflow = restate.Workflow(f"JtbdOrchestrator{suffix}")
        parent_target = f"JtbdOrchestrator{suffix}/" + workflow_key + "/draft_for_jtbd"
        fake_jtbd_application_client = FakeJtbdApplicationClient()
        restate_draft_for_jtbd = workflows.RestateDraftForJtbd(
            jtbd_orchestrator_workflow,
            activities.RestateMarkJtbdDrafting(jtbd_actions_service, fake_jtbd_application_client),
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
                        restate_draft_for_jtbd.handler, key="other-" + workflow_key, arg=relays.DraftForJtbdRequest(jtbd_id=workflow_key, description="design-feature", status="drafting")
                    )
                draft_for_jtbd_response = await restate_client.Client(async_client).workflow_call(
                    restate_draft_for_jtbd.handler, key=workflow_key, arg=relays.DraftForJtbdRequest(jtbd_id=workflow_key, description="design-feature", status="drafting")
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
            assert draft_for_jtbd_response == relays.DraftForJtbdResponse(jtbd_id=workflow_key)
            assert [recorded.jtbd_id for recorded in fake_jtbd_application_client.recorded] == [workflow_key]
            assert [(row["target"], row["completion_result"]) for row in invoked.json()["rows"]] == [
                (f"JtbdActions{suffix}/mark_jtbd_drafting", "success")
            ]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
