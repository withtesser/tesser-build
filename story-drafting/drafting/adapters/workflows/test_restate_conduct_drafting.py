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


class TestRestateConductDrafting:

    async def test_conduct_drafting_writes_and_keeps_the_stories_then_waits_on_the_pick_promise(self) -> None:
        drafting_id = uuid.uuid4().hex
        suffix = uuid.uuid4().hex
        writing_actions_service = restate.Service(f"WritingActions{suffix}")
        drafting_actions_service = restate.Service(f"DraftingActions{suffix}")
        drafting_orchestrator_workflow = restate.Workflow(f"DraftingOrchestrator{suffix}")
        fake_writing_application_client = FakeWritingApplicationClient()
        fake_drafting_application_client = FakeDraftingApplicationClient()
        restate_conduct_drafting = workflows.RestateConductDrafting(
            drafting_orchestrator_workflow,
            activities.RestateWriteStories(writing_actions_service, fake_writing_application_client),
            activities.RestateKeepDraftedStories(drafting_actions_service, fake_drafting_application_client),
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

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                sent = await restate_client.Client(async_client).workflow_send(
                    restate_conduct_drafting.handler,
                    key=drafting_id,
                    arg=relays.ConductDraftingRequest(drafting_id=drafting_id, job="a job"),
                )
            awaited: list[str] = []
            for _ in range(100):
                journaled = await admin.post(
                    "/query",
                    headers={"accept": "application/json"},
                    json={
                        "query": "SELECT j.entry_lite_json FROM sys_journal j JOIN sys_invocation i ON j.id = i.id "
                        f"WHERE i.target = 'DraftingOrchestrator{suffix}/{drafting_id}/conduct_drafting' "
                        "AND j.entry_type = 'Command: GetPromise'"
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
            assert fake_writing_application_client.jobs == ["a job"]
            assert fake_drafting_application_client.kept == [(drafting_id, ("first", "second"))]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)

    async def test_a_drafting_its_key_does_not_name_ends_terminally_before_anything_is_written(self) -> None:
        drafting_id = uuid.uuid4().hex
        suffix = uuid.uuid4().hex
        writing_actions_service = restate.Service(f"WritingActions{suffix}")
        drafting_actions_service = restate.Service(f"DraftingActions{suffix}")
        drafting_orchestrator_workflow = restate.Workflow(f"DraftingOrchestrator{suffix}")
        fake_writing_application_client = FakeWritingApplicationClient()
        fake_drafting_application_client = FakeDraftingApplicationClient()
        restate_conduct_drafting = workflows.RestateConductDrafting(
            drafting_orchestrator_workflow,
            activities.RestateWriteStories(writing_actions_service, fake_writing_application_client),
            activities.RestateKeepDraftedStories(drafting_actions_service, fake_drafting_application_client),
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

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                with pytest.raises(restate.HttpError) as foreign:
                    await restate_client.Client(async_client).workflow_call(
                        restate_conduct_drafting.handler,
                        key="other-" + drafting_id,
                        arg=relays.ConductDraftingRequest(drafting_id=drafting_id, job="a job"),
                    )

            assert foreign.value.status_code == 400
            assert fake_writing_application_client.jobs == []
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
