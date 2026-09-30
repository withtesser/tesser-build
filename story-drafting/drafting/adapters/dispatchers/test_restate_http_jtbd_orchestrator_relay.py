# pragma: tesser-generated; regenerate from the composition, never edit by hand
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
class FakeStoryApplicationClient(client.StoryApplicationClient):

    def __init__(self) -> None:
        self.received: list[relays.DraftStoriesRequest] = []

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        self.received.append(draft_stories_request)
        return relays.DraftStoriesResponse(story_texts=(relays.StoryText(given="a job to be done", when="I submit it", then="it is drafting"),))


@ts.fake
class FakeJtbdApplicationClient(client.JtbdApplicationClient):

    def __init__(self) -> None:
        self.received: list[relays.RecordStoriesRequest] = []

    async def record_stories(self, record_stories_request: relays.RecordStoriesRequest) -> relays.RecordStoriesResponse:
        self.received.append(record_stories_request)
        return relays.RecordStoriesResponse(jtbd_id=record_stories_request.jtbd_id)


class TestRestateHttpJtbdOrchestratorRelay:

    async def test_start_conduct_story_drafting_starts_the_workflow_the_engine_keys_by_the_jtbd_id_and_does_not_wait(self) -> None:
        workflow_key = "../admin?x=1#f-" + str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        story_actions_service = restate.Service(f"StoryActions{suffix}")
        jtbd_actions_service = restate.Service(f"JtbdActions{suffix}")
        jtbd_orchestrator_workflow = restate.Workflow(f"JtbdOrchestrator{suffix}")
        restate_conduct_story_drafting = workflows.RestateConductStoryDrafting(
            jtbd_orchestrator_workflow,
            activities.RestateDraftStories(story_actions_service, FakeStoryApplicationClient()),
            activities.RestateRecordStories(jtbd_actions_service, FakeJtbdApplicationClient()),
        )
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([story_actions_service, jtbd_actions_service, jtbd_orchestrator_workflow])),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        admin = httpx.AsyncClient(base_url=os.environ["RESTATE_ADMIN"], timeout=10.0)
        registered = httpx.Response(503)
        started: list[dict[str, str]] = []
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

            start_conduct_story_drafting_response = await dispatchers.RestateHttpJtbdOrchestratorRelay(
                os.environ["RESTATE_INGRESS"], restate_conduct_story_drafting
            ).start_conduct_story_drafting(relays.ConductStoryDraftingRequest(jtbd_id=workflow_key, role="a developer", i_want="stories drafted", so_that="I can accept them"))
            for _ in range(100):
                invoked = await admin.post(
                    "/query",
                    headers={"accept": "application/json"},
                    json={
                        "query": "SELECT id, target_service_key, invoked_by, status FROM sys_invocation "
                        f"WHERE target_service_name = 'JtbdOrchestrator{suffix}'"
                    },
                )
                started = invoked.json()["rows"]
                if started:
                    break
                await asyncio.sleep(0.1)

            assert start_conduct_story_drafting_response == relays.StartConductStoryDraftingResponse(jtbd_id=workflow_key)
            assert [(row["target_service_key"], row["invoked_by"], row["status"] != "completed") for row in started] == [
                (workflow_key, "ingress", True)
            ]
        finally:
            for row in started:
                await admin.patch(f"/invocations/{row['id']}/kill")
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
