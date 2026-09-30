# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import asyncio
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

    def __init__(self, released: asyncio.Event) -> None:
        self.released = released
        self.received: list[relays.DraftStoriesRequest] = []

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        self.received.append(draft_stories_request)
        await asyncio.wait_for(self.released.wait(), timeout=30.0)
        return relays.DraftStoriesResponse(story_texts=(relays.StoryText(given="a job to be done", when="I submit it", then="it is drafting its stories"),))


@ts.fake
class FakeJtbdApplicationClient(client.JtbdApplicationClient):

    def __init__(self, released: asyncio.Event) -> None:
        self.released = released
        self.received: list[relays.RecordDraftedStoriesRequest] = []

    async def record_drafted_stories(self, record_drafted_stories_request: relays.RecordDraftedStoriesRequest) -> relays.RecordDraftedStoriesResponse:
        self.received.append(record_drafted_stories_request)
        await asyncio.wait_for(self.released.wait(), timeout=30.0)
        return relays.RecordDraftedStoriesResponse(jtbd_id=record_drafted_stories_request.jtbd_id)


class TestRestateHttpJtbdOrchestratorRelay:

    async def test_start_story_drafting_starts_the_workflow_the_engine_keys_by_the_jtbd_id_and_does_not_wait(
        self, engine_url: str, engine_admin_url: str, engine_callback_host: str, free_port: int
    ) -> None:
        workflow_key = "../admin?x=1#f-" + str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        released = asyncio.Event()
        story_actions_service = restate.Service(f"StoryActions{suffix}")
        jtbd_actions_service = restate.Service(f"JtbdActions{suffix}")
        jtbd_orchestrator_workflow = restate.Workflow(f"JtbdOrchestrator{suffix}")
        restate_story_drafting = workflows.RestateStoryDrafting(
            jtbd_orchestrator_workflow,
            activities.RestateDraftStories(story_actions_service, FakeStoryApplicationClient(released)),
            activities.RestateRecordDraftedStories(jtbd_actions_service, FakeJtbdApplicationClient(released)),
        )
        port = free_port
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
        admin = httpx.AsyncClient(base_url=engine_admin_url, timeout=10.0)
        registered = httpx.Response(503)
        started: list[dict[str, str]] = []
        try:
            registering_until = asyncio.get_running_loop().time() + 30.0
            while True:
                registered = await admin.post(
                    "/deployments",
                    json={"uri": f"http://{engine_callback_host}:{port}", "force": True},
                )
                if registered.is_success or asyncio.get_running_loop().time() > registering_until:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            try:
                start_story_drafting_response = await asyncio.wait_for(
                    dispatchers.RestateHttpJtbdOrchestratorRelay(engine_url, restate_story_drafting).start_story_drafting(
                        relays.StoryDraftingRequest(jtbd_id=workflow_key, role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back")
                    ),
                    timeout=15.0,
                )
            except TimeoutError as timed_out:
                raise AssertionError(
                    "start_story_drafting did not return within 15 s although the workflow is held at its first step: "
                    "the relay waits for the workflow to finish"
                ) from timed_out
            polling_until = asyncio.get_running_loop().time() + 30.0
            while asyncio.get_running_loop().time() < polling_until:
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

            assert start_story_drafting_response == relays.StartStoryDraftingResponse(jtbd_id=workflow_key)
            assert [(row["target_service_key"], row["invoked_by"], row["status"] != "completed") for row in started] == [
                (workflow_key, "ingress", True)
            ]
        finally:
            released.set()
            for row in started:
                await admin.patch(f"/invocations/{row['id']}/kill")
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.wait_for(asyncio.gather(serving, return_exceptions=True), timeout=5.0)
