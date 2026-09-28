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
        self.kept: list[tuple[str, str]] = []
        self.offered: list[tuple[str, tuple[str, ...]]] = []

    async def keep_run(self, keep_run_request: relays.KeepRunRequest) -> relays.KeepRunResponse:
        self.kept.append((keep_run_request.run_id, keep_run_request.job))
        return relays.KeepRunResponse(run_id=keep_run_request.run_id)

    async def offer_stories(self, offer_stories_request: relays.OfferStoriesRequest) -> relays.OfferStoriesResponse:
        self.offered.append((offer_stories_request.run_id, offer_stories_request.stories))
        return relays.OfferStoriesResponse(run_id=offer_stories_request.run_id)


@ts.fake
class FakeDrafterApplicationClient(client.DrafterApplicationClient):

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        return relays.WriteStoriesResponse(stories=("a story",))


class TestRestateHttpRunOrchestratorRelay:

    async def test_starting_sends_the_workflow_keyed_by_the_run_id_and_the_engine_keeps_and_offers_the_run(self) -> None:
        run_id = "a/b " + uuid.uuid4().hex
        suffix = uuid.uuid4().hex
        run_actions_service = restate.Service(f"RunActions{suffix}")
        drafter_actions_service = restate.Service(f"DrafterActions{suffix}")
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        fake_run_application_client = FakeRunApplicationClient()
        restate_http_run_orchestrator_relay = dispatchers.RestateHttpRunOrchestratorRelay(
            os.environ["RESTATE_INGRESS"],
            workflows.RestateDraftStories(
                run_orchestrator_workflow,
                activities.RestateKeepRun(run_actions_service, fake_run_application_client),
                activities.RestateOfferStories(run_actions_service, fake_run_application_client),
                activities.RestateWriteStories(drafter_actions_service, FakeDrafterApplicationClient()),
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
                typing.cast(
                    hypercorn_typing.ASGIFramework,
                    restate.app([run_actions_service, drafter_actions_service, run_orchestrator_workflow]),
                ),
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

            start_draft_stories_response = await restate_http_run_orchestrator_relay.start_draft_stories(
                relays.DraftStoriesRequest(run_id=domain.RunId(run_id), job=domain.Job("a job"))
            )
            for _ in range(100):
                if fake_run_application_client.offered:
                    break
                await asyncio.sleep(0.05)
            keyed = await admin.post(
                "/query",
                headers={"accept": "application/json"},
                json={
                    "query": "SELECT id, target_service_key FROM sys_invocation "
                    f"WHERE target_service_name = 'RunOrchestrator{suffix}'"
                },
            )
            for row in keyed.json()["rows"]:
                await admin.patch(f"/invocations/{row['id']}/kill")

            assert start_draft_stories_response == relays.StartDraftStoriesResponse(run_id=run_id)
            assert fake_run_application_client.kept == [(run_id, "a job")]
            assert fake_run_application_client.offered == [(run_id, ("a story",))]
            assert [row["target_service_key"] for row in keyed.json()["rows"]] == [run_id]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
