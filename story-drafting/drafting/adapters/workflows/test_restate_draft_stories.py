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


@ts.fake
class FakeRunApplicationClient(client.RunApplicationClient):

    def __init__(self) -> None:
        self.recorded: list[relays.RecordRunRequest] = []

    async def record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        self.recorded.append(record_run_request)
        return relays.RecordRunResponse(run_id=record_run_request.run_id)


@ts.fake
class FakeStoryWritingApplicationClient(client.StoryWritingApplicationClient):

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        return relays.WriteStoriesResponse(stories=("As a developer, I want " + write_stories_request.job,))


class TestRestateDraftStories:

    async def test_draft_stories_records_the_drafted_run_through_the_engine_then_waits_on_the_pick(self) -> None:
        workflow_key = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        run_actions_service = restate.Service(f"RunActions{suffix}")
        story_writing_actions_service = restate.Service(f"StoryWritingActions{suffix}")
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        fake_run_application_client = FakeRunApplicationClient()
        restate_draft_stories = workflows.RestateDraftStories(
            run_orchestrator_workflow,
            activities.RestateRecordRun(run_actions_service, fake_run_application_client),
            activities.RestateWriteStories(story_writing_actions_service, FakeStoryWritingApplicationClient()),
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
                    restate.app([run_actions_service, story_writing_actions_service, run_orchestrator_workflow]),
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
                    json={"uri": f"http://{os.environ['RESTATE_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                sent = await restate_client.Client(async_client).workflow_send(
                    restate_draft_stories.handler,
                    key=workflow_key,
                    arg=relays.DraftStoriesRequest(run_id=workflow_key, job="plan a migration", stage="drafting"),
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

            assert awaited == [relays.PICK_STORIES_PROMISE]
            assert [
                (recorded.stage, recorded.stories, recorded.accepted_stories)
                for recorded in fake_run_application_client.recorded
            ] == [
                ("drafting", (), ()),
                ("awaiting_pick", ("As a developer, I want plan a migration",), ()),
            ]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)

    async def test_a_draft_its_key_does_not_name_ends_terminally_before_anything_is_recorded(self) -> None:
        workflow_key = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        run_actions_service = restate.Service(f"RunActions{suffix}")
        story_writing_actions_service = restate.Service(f"StoryWritingActions{suffix}")
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        fake_run_application_client = FakeRunApplicationClient()
        restate_draft_stories = workflows.RestateDraftStories(
            run_orchestrator_workflow,
            activities.RestateRecordRun(run_actions_service, fake_run_application_client),
            activities.RestateWriteStories(story_writing_actions_service, FakeStoryWritingApplicationClient()),
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
                    restate.app([run_actions_service, story_writing_actions_service, run_orchestrator_workflow]),
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
                    json={"uri": f"http://{os.environ['RESTATE_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                with pytest.raises(restate.HttpError) as foreign:
                    await restate_client.Client(async_client).workflow_call(
                        restate_draft_stories.handler,
                        key="other-" + workflow_key,
                        arg=relays.DraftStoriesRequest(run_id=workflow_key, job="plan a migration", stage="drafting"),
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
