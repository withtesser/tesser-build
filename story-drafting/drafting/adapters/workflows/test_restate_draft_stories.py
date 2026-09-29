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
import pytest
import restate
import restate.client as restate_client

import drafting.adapters.activities as activities
import drafting.adapters.workflows as workflows
import drafting.application.client as client
import drafting.application.relays as relays
import drafting.domain as domain


@ts.fake
class FakeRunApplicationClient(client.RunApplicationClient):

    def __init__(self) -> None:
        self.recorded: list[tuple[str, str]] = []

    async def record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        self.recorded.append((str(record_run_request.run.identity), str(record_run_request.run.stage)))
        return relays.RecordRunResponse(run_id=str(record_run_request.run.identity))


@ts.fake
class FakeStoryApplicationClient(client.StoryApplicationClient):

    def __init__(self) -> None:
        self.jobs: list[str] = []

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        self.jobs.append(write_stories_request.job)
        return relays.WriteStoriesResponse(stories=("a story",))


class TestRestateDraftStories:

    async def test_draft_stories_records_the_drafted_run_then_waits_on_the_promise_the_relays_name_and_refuses_a_foreign_key(self) -> None:
        run_id = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        run_actions_service = restate.Service(f"RunActions{suffix}")
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        story_actions_service = restate.Service(f"StoryActions{suffix}")
        fake_run_application_client = FakeRunApplicationClient()
        fake_story_application_client = FakeStoryApplicationClient()
        restate_draft_stories = workflows.RestateDraftStories(
            run_orchestrator_workflow,
            activities.RestateRecordRun(run_actions_service, fake_run_application_client),
            activities.RestateWriteStories(story_actions_service, fake_story_application_client),
        )
        first = int(os.environ["STORY_DRAFTING_PORT"])
        port = 0
        for candidate in range(first + 1, first + 10):
            with socket.socket() as probe:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    probe.bind(("0.0.0.0", candidate))
                except OSError:
                    continue
                port = candidate
                break
        assert port, f"no free port in {first + 1}-{first + 9}"
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([run_actions_service, story_actions_service, run_orchestrator_workflow])),
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

            run = domain.Run(domain.RunSpec(run_id=run_id, job="ship", stage="drafting", stories=(), accepted_stories=()))
            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                sent = await restate_client.Client(async_client).workflow_send(
                    restate_draft_stories.handler, key=run_id, arg=relays.DraftStoriesRequest(run=run)
                )
                with pytest.raises(restate.HttpError) as foreign:
                    await restate_client.Client(async_client).workflow_call(
                        restate_draft_stories.handler, key="other-" + run_id, arg=relays.DraftStoriesRequest(run=run)
                    )

            awaited: list[str] = []
            for _ in range(100):
                journaled = await admin.post(
                    "/query",
                    headers={"accept": "application/json"},
                    json={
                        "query": "SELECT entry_lite_json FROM sys_journal "
                        f"WHERE id = '{sent.invocation_id}' AND entry_type = 'Command: GetPromise'"
                    },
                )
                awaited = [
                    json.loads(row["entry_lite_json"])["Command"]["GetPromise"]["key"] for row in journaled.json()["rows"]
                ]
                if awaited:
                    break
                await asyncio.sleep(0.05)
            await admin.patch(f"/invocations/{sent.invocation_id}/kill")

            assert awaited == [relays.PICK_STORY_PROMISE]
            assert fake_run_application_client.recorded == [(run_id, "drafting"), (run_id, "awaiting_pick")]
            assert fake_story_application_client.jobs == ["ship"]
            assert foreign.value.status_code == 400
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
