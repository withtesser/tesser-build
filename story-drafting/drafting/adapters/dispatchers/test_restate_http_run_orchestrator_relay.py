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

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        return relays.WriteStoriesResponse(stories=("a story",))


class TestRestateHttpRunOrchestratorRelay:

    async def test_starting_draft_stories_answers_at_once_and_the_workflow_goes_on_to_record_the_drafted_run(self) -> None:
        run_id = "run/" + uuid.uuid4().hex
        suffix = uuid.uuid4().hex
        run_actions_service = restate.Service(f"RunActions{suffix}")
        story_actions_service = restate.Service(f"StoryActions{suffix}")
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        fake_run_application_client = FakeRunApplicationClient()
        restate_http_run_orchestrator_relay = dispatchers.RestateHttpRunOrchestratorRelay(
            os.environ["RESTATE_URL"],
            workflows.RestateDraftStories(
                run_orchestrator_workflow,
                activities.RestateRecordRun(run_actions_service, fake_run_application_client),
                activities.RestateWriteStories(story_actions_service, FakeStoryApplicationClient()),
            ),
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
            start_draft_stories_response = await restate_http_run_orchestrator_relay.start_draft_stories(
                relays.DraftStoriesRequest(run=run)
            )
            for _ in range(100):
                if len(fake_run_application_client.recorded) == 2:
                    break
                await asyncio.sleep(0.05)
            running = await admin.post(
                "/query",
                headers={"accept": "application/json"},
                json={
                    "query": "SELECT id FROM sys_invocation "
                    f"WHERE target_service_name = '{run_orchestrator_workflow.name}' "
                    f"AND target_service_key = '{run_id}'"
                },
            )
            for row in running.json()["rows"]:
                await admin.patch(f"/invocations/{row['id']}/kill")

            assert start_draft_stories_response == relays.StartDraftStoriesResponse(run_id=run_id)
            assert fake_run_application_client.recorded == [(run_id, "drafting"), (run_id, "awaiting_pick")]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
