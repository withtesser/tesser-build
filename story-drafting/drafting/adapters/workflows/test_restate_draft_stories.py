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

import drafting.adapters.activities as activities
import drafting.adapters.workflows as workflows
import drafting.application.client as client
import drafting.application.relays as relays
import drafting.domain as domain


@ts.fake
class FakeRunApplicationClient(client.RunApplicationClient):

    def __init__(self) -> None:
        self.kept: list[tuple[str, str]] = []

    async def keep_run(self, keep_run_request: relays.KeepRunRequest) -> relays.KeepRunResponse:
        self.kept.append((keep_run_request.run_id, keep_run_request.job))
        return relays.KeepRunResponse(run_id=keep_run_request.run_id)


class TestRestateDraftStories:

    async def test_draft_stories_keeps_the_run_through_the_engine_and_a_foreign_key_ends_terminally(self) -> None:
        run_id = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        run_actions_service = restate.Service(f"RunActions{suffix}")
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        fake_run_application_client = FakeRunApplicationClient()
        restate_draft_stories = workflows.RestateDraftStories(
            run_orchestrator_workflow,
            activities.RestateKeepRun(run_actions_service, fake_run_application_client),
        )
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([run_actions_service, run_orchestrator_workflow])),
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

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                draft_stories_response = await restate_client.Client(async_client).workflow_call(
                    restate_draft_stories.handler,
                    key=run_id,
                    arg=relays.DraftStoriesRequest(run_id=domain.RunId(run_id), job=domain.Job("a job")),
                )
                with pytest.raises(restate.HttpError) as foreign:
                    await restate_client.Client(async_client).workflow_call(
                        restate_draft_stories.handler,
                        key="other-" + run_id,
                        arg=relays.DraftStoriesRequest(run_id=domain.RunId(run_id), job=domain.Job("a job")),
                    )

            assert draft_stories_response == relays.DraftStoriesResponse(run_id=run_id)
            assert fake_run_application_client.kept == [(run_id, "a job")]
            assert foreign.value.status_code == 400
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
