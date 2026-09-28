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


@ts.fake
class FakeDraftingApplicationClient(client.DraftingApplicationClient):

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        return relays.DraftStoriesResponse(stories=(f"a story about {draft_stories_request.job}",))


@ts.fake
class FakeRunApplicationClient(client.RunApplicationClient):

    def __init__(self) -> None:
        self.recorded: list[relays.RecordRunRequest] = []

    async def record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        self.recorded.append(record_run_request)
        return relays.RecordRunResponse(run_id=record_run_request.run_id)


class TestRestateConductRun:

    async def test_a_run_records_its_drafted_stories_then_waits_on_the_pick(self) -> None:
        run_id = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        drafting_actions_service = restate.Service(f"DraftingActions{suffix}")
        run_actions_service = restate.Service(f"RunActions{suffix}")
        fake_run_application_client = FakeRunApplicationClient()
        restate_conduct_run = workflows.RestateConductRun(
            run_orchestrator_workflow,
            activities.RestateDraftStories(drafting_actions_service, FakeDraftingApplicationClient()),
            activities.RestateRecordRun(run_actions_service, fake_run_application_client),
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

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                await restate_client.Client(async_client).workflow_send(
                    restate_conduct_run.handler, key=run_id, arg=relays.ConductRunRequest(run_id=run_id, job="ship it")
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
                waiting = [row["status"] for row in invocations] in (["running"], ["suspended"])
                if waiting and fake_run_application_client.recorded:
                    break
                await asyncio.sleep(0.05)

            assert fake_run_application_client.recorded == [
                relays.RecordRunRequest(
                    run_id=run_id,
                    job="ship it",
                    step="awaiting_pick",
                    drafted_stories=("a story about ship it",),
                    accepted_stories=(),
                )
            ]
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

    async def test_a_run_its_key_does_not_name_is_refused(self) -> None:
        run_id = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        drafting_actions_service = restate.Service(f"DraftingActions{suffix}")
        run_actions_service = restate.Service(f"RunActions{suffix}")
        fake_run_application_client = FakeRunApplicationClient()
        restate_conduct_run = workflows.RestateConductRun(
            run_orchestrator_workflow,
            activities.RestateDraftStories(drafting_actions_service, FakeDraftingApplicationClient()),
            activities.RestateRecordRun(run_actions_service, fake_run_application_client),
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
                with pytest.raises(restate.HttpError) as foreign:
                    await restate_client.Client(async_client).workflow_call(
                        restate_conduct_run.handler,
                        key="other-" + run_id,
                        arg=relays.ConductRunRequest(run_id=run_id, job="ship it"),
                    )

            assert foreign.value.status_code == 400
            assert fake_run_application_client.recorded == []
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
