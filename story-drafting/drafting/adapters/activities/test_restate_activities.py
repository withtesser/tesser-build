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
import restate.client as restate_client

import drafting.adapters.activities as activities
import drafting.application.client as client
import drafting.application.relays as relays


@ts.fake
class FakeDraftingApplicationClient(client.DraftingApplicationClient):

    def __init__(self) -> None:
        self.asked: list[relays.DraftStoriesRequest] = []

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        self.asked.append(draft_stories_request)
        return relays.DraftStoriesResponse(stories=(f"a story about {draft_stories_request.job}",))


@ts.fake
class FakeRunApplicationClient(client.RunApplicationClient):

    def __init__(self) -> None:
        self.recorded: list[relays.RecordRunRequest] = []

    async def record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        self.recorded.append(record_run_request)
        return relays.RecordRunResponse(run_id=record_run_request.run_id)


class TestRestateDraftStories:

    async def test_restate_serves_draft_stories_and_a_call_made_with_its_handler_reaches_the_application_client(
        self,
    ) -> None:
        drafting_actions_service = restate.Service(f"DraftingActions{uuid.uuid4().hex}")
        fake_drafting_application_client = FakeDraftingApplicationClient()
        restate_draft_stories = activities.RestateDraftStories(
            drafting_actions_service, fake_drafting_application_client
        )
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([drafting_actions_service])),
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
                draft_stories_response = await restate_client.Client(async_client).service_call(
                    restate_draft_stories.handler, relays.DraftStoriesRequest(run_id="r1", job="ship it")
                )

            assert draft_stories_response == relays.DraftStoriesResponse(stories=("a story about ship it",))
            assert [request.job for request in fake_drafting_application_client.asked] == ["ship it"]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)


class TestRestateRecordRun:

    async def test_restate_serves_record_run_and_a_call_made_with_its_handler_reaches_the_application_client(
        self,
    ) -> None:
        run_actions_service = restate.Service(f"RunActions{uuid.uuid4().hex}")
        fake_run_application_client = FakeRunApplicationClient()
        restate_record_run = activities.RestateRecordRun(run_actions_service, fake_run_application_client)
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([run_actions_service])),
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
                record_run_response = await restate_client.Client(async_client).service_call(
                    restate_record_run.handler,
                    relays.RecordRunRequest(
                        run_id="r1",
                        job="ship it",
                        step="awaiting_pick",
                        drafted_stories=("a story",),
                        accepted_stories=(),
                    ),
                )

            assert record_run_response == relays.RecordRunResponse(run_id="r1")
            assert [request.run_id for request in fake_run_application_client.recorded] == ["r1"]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
