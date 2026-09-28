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
class FakeDraftingApplicationClient(client.DraftingApplicationClient):

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        return relays.DraftStoriesResponse(stories=(f"a story about {draft_stories_request.job}",))


@ts.fake
class FakeRunApplicationClient(client.RunApplicationClient):

    async def record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        return relays.RecordRunResponse(run_id=record_run_request.run_id)


class TestRestateHttpRunOrchestratorRelay:

    async def test_starting_a_run_answers_while_the_run_it_keys_waits_for_the_pick(self) -> None:
        run_id = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        drafting_actions_service = restate.Service(f"DraftingActions{suffix}")
        run_actions_service = restate.Service(f"RunActions{suffix}")
        restate_http_run_orchestrator_relay = dispatchers.RestateHttpRunOrchestratorRelay(
            os.environ["RESTATE_INGRESS"],
            workflows.RestateConductRun(
                run_orchestrator_workflow,
                activities.RestateDraftStories(drafting_actions_service, FakeDraftingApplicationClient()),
                activities.RestateRecordRun(run_actions_service, FakeRunApplicationClient()),
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
                    restate.app([run_orchestrator_workflow, drafting_actions_service, run_actions_service]),
                ),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        admin = httpx.AsyncClient(base_url=os.environ["RESTATE_ADMIN"], timeout=10.0)
        registered = httpx.Response(503)
        invocations: list[dict[str, str]] = []
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

            start_conduct_run_response = await restate_http_run_orchestrator_relay.start_conduct_run(
                relays.ConductRunRequest(run_id=run_id, job="ship it")
            )
            for _ in range(100):
                queried = await admin.post(
                    "/query",
                    headers={"accept": "application/json"},
                    json={
                        "query": "SELECT id, status FROM sys_invocation "
                        f"WHERE target = 'RunOrchestrator{suffix}/{run_id}/conduct_run'"
                    },
                )
                invocations = queried.json()["rows"]
                if [row["status"] for row in invocations] in (["running"], ["suspended"]):
                    break
                await asyncio.sleep(0.05)

            assert start_conduct_run_response == relays.StartConductRunResponse(run_id=run_id)
            assert [row["status"] for row in invocations] in (["running"], ["suspended"])
        finally:
            for row in invocations:
                await admin.patch(f"/invocations/{row['id']}/kill")
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
