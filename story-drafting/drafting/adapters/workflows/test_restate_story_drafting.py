# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import asyncio
import json
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

import drafting.adapters.activities as activities
import drafting.adapters.workflows as workflows
import drafting.application.client as client
import drafting.application.relays as relays


@ts.fake
class FakeStoryApplicationClient(client.StoryApplicationClient):

    def __init__(self) -> None:
        self.received: list[relays.DraftStoriesRequest] = []

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        self.received.append(draft_stories_request)
        return relays.DraftStoriesResponse(story_texts=(relays.StoryText(given="a job to be done", when="I submit it", then="it is drafting its stories"),))


@ts.fake
class FakeJtbdApplicationClient(client.JtbdApplicationClient):

    def __init__(self) -> None:
        self.received: list[relays.RecordDraftedStoriesRequest] = []

    async def record_drafted_stories(self, record_drafted_stories_request: relays.RecordDraftedStoriesRequest) -> relays.RecordDraftedStoriesResponse:
        self.received.append(record_drafted_stories_request)
        return relays.RecordDraftedStoriesResponse(jtbd_id=record_drafted_stories_request.jtbd_id)


class TestRestateStoryDrafting:

    async def test_story_drafting_runs_its_steps_in_order(
        self, engine_url: str, engine_admin_url: str, engine_callback_host: str, free_port: int
    ) -> None:
        workflow_key = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        story_actions_service = restate.Service(f"StoryActions{suffix}")
        jtbd_actions_service = restate.Service(f"JtbdActions{suffix}")
        jtbd_orchestrator_workflow = restate.Workflow(f"JtbdOrchestrator{suffix}")
        parent_target = f"JtbdOrchestrator{suffix}/" + workflow_key + "/story_drafting"
        fake_story_application_client = FakeStoryApplicationClient()
        fake_jtbd_application_client = FakeJtbdApplicationClient()
        restate_story_drafting = workflows.RestateStoryDrafting(
            jtbd_orchestrator_workflow,
            activities.RestateDraftStories(story_actions_service, fake_story_application_client),
            activities.RestateRecordDraftedStories(jtbd_actions_service, fake_jtbd_application_client),
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
        waiting: list[dict[str, str]] = []
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

            async with httpx.AsyncClient(base_url=engine_url, timeout=30.0) as async_client:
                with pytest.raises(restate.HttpError) as foreign:
                    await restate_client.Client(async_client).workflow_call(
                        restate_story_drafting.handler,
                        key="other-" + workflow_key,
                        arg=relays.StoryDraftingRequest(jtbd_id=workflow_key, role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back"),
                    )
                await restate_client.Client(async_client).workflow_send(
                    restate_story_drafting.handler,
                    key=workflow_key,
                    arg=relays.StoryDraftingRequest(jtbd_id=workflow_key, role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back"),
                )
            invoked = httpx.Response(503)
            polling_until = asyncio.get_running_loop().time() + 30.0
            while asyncio.get_running_loop().time() < polling_until:
                invoked = await admin.post(
                    "/query",
                    headers={"accept": "application/json"},
                    json={
                        "query": "SELECT target, completion_result FROM sys_invocation "
                        "WHERE invoked_by_target = '" + parent_target + "' ORDER BY created_at"
                    },
                )
                if [row.get("completion_result") for row in invoked.json()["rows"]] == ["success", "success", ]:
                    break
                await asyncio.sleep(0.1)

            assert foreign.value.status_code == 400
            assert [
                (row["status"] in ("running", "suspended"), json.loads(row["entry_lite_json"])["Command"]["GetPromise"]["key"])
                for row in waiting
            ] == []
            assert [received.jtbd_id for received in fake_story_application_client.received] == [workflow_key, ]
            assert [received.jtbd_id for received in fake_jtbd_application_client.received] == [workflow_key, ]
            assert [(row["target"], row.get("completion_result")) for row in invoked.json()["rows"]] == [
                (f"StoryActions{suffix}/draft_stories", "success"),
                (f"JtbdActions{suffix}/record_drafted_stories", "success"),
            ]
        finally:
            for row in waiting:
                await admin.patch(f"/invocations/{row['id']}/kill")
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.wait_for(asyncio.gather(serving, return_exceptions=True), timeout=5.0)
