from __future__ import annotations

import asyncio
import json
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
class FakeWritingApplicationClient(client.WritingApplicationClient):

    def __init__(self) -> None:
        self.jobs: list[str] = []

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        self.jobs.append(write_stories_request.job)
        return relays.WriteStoriesResponse(texts=("first", "second"))


@ts.fake
class FakeDraftingApplicationClient(client.DraftingApplicationClient):

    def __init__(self) -> None:
        self.kept: list[tuple[str, tuple[str, ...]]] = []

    async def keep_drafted_stories(
        self, keep_drafted_stories_request: relays.KeepDraftedStoriesRequest
    ) -> relays.KeepDraftedStoriesResponse:
        self.kept.append((keep_drafted_stories_request.drafting_id, keep_drafted_stories_request.texts))
        return relays.KeepDraftedStoriesResponse(drafting_id=keep_drafted_stories_request.drafting_id)


class TestRestateHttpDraftingOrchestratorRelay:

    async def test_starting_answers_at_once_and_the_drafting_runs_on_to_wait_for_the_pick(self) -> None:
        drafting_id = "d.1"
        suffix = uuid.uuid4().hex
        writing_actions_service = restate.Service(f"WritingActions{suffix}")
        drafting_actions_service = restate.Service(f"DraftingActions{suffix}")
        drafting_orchestrator_workflow = restate.Workflow(f"DraftingOrchestrator{suffix}")
        fake_writing_application_client = FakeWritingApplicationClient()
        fake_drafting_application_client = FakeDraftingApplicationClient()
        restate_http_drafting_orchestrator_relay = dispatchers.RestateHttpDraftingOrchestratorRelay(
            os.environ["RESTATE_INGRESS"],
            workflows.RestateConductDrafting(
                drafting_orchestrator_workflow,
                activities.RestateWriteStories(writing_actions_service, fake_writing_application_client),
                activities.RestateKeepDraftedStories(drafting_actions_service, fake_drafting_application_client),
            ),
        )
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([writing_actions_service, drafting_actions_service, drafting_orchestrator_workflow])),
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
                    json={"uri": f"http://{os.environ['STORY_DRAFTING_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            start_conduct_drafting_response = await restate_http_drafting_orchestrator_relay.start_conduct_drafting(
                relays.ConductDraftingRequest(drafting_id=drafting_id, job="a job")
            )
            awaited: list[str] = []
            invocation_ids: list[str] = []
            for _ in range(100):
                journaled = await admin.post(
                    "/query",
                    headers={"accept": "application/json"},
                    json={
                        "query": "SELECT i.id, j.entry_lite_json FROM sys_journal j JOIN sys_invocation i ON j.id = i.id "
                        f"WHERE i.target = 'DraftingOrchestrator{suffix}/{drafting_id}/conduct_drafting' "
                        "AND j.entry_type = 'Command: GetPromise'"
                    },
                )
                awaited = [
                    json.loads(row["entry_lite_json"])["Command"]["GetPromise"]["key"] for row in journaled.json()["rows"]
                ]
                invocation_ids = [row["id"] for row in journaled.json()["rows"]]
                if awaited:
                    break
                await asyncio.sleep(0.05)
            for invocation_id in invocation_ids:
                await admin.patch(f"/invocations/{invocation_id}/kill")

            assert start_conduct_drafting_response == relays.StartConductDraftingResponse(drafting_id=drafting_id)
            assert awaited == [relays.PICK_STORY_PROMISE]
            assert fake_drafting_application_client.kept == [(drafting_id, ("first", "second"))]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
