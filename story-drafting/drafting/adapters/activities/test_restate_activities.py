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


class TestRestateActivities:

    async def test_restate_serves_each_action_and_a_call_made_with_its_handler_reaches_its_application_client(
        self,
    ) -> None:
        suffix = uuid.uuid4().hex
        writing_actions_service = restate.Service(f"WritingActions{suffix}")
        drafting_actions_service = restate.Service(f"DraftingActions{suffix}")
        fake_writing_application_client = FakeWritingApplicationClient()
        fake_drafting_application_client = FakeDraftingApplicationClient()
        restate_write_stories = activities.RestateWriteStories(writing_actions_service, fake_writing_application_client)
        restate_keep_drafted_stories = activities.RestateKeepDraftedStories(
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
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([writing_actions_service, drafting_actions_service])),
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
                write_stories_response = await restate_client.Client(async_client).service_call(
                    restate_write_stories.handler, relays.WriteStoriesRequest(job="a job")
                )
                keep_drafted_stories_response = await restate_client.Client(async_client).service_call(
                    restate_keep_drafted_stories.handler,
                    relays.KeepDraftedStoriesRequest(drafting_id="d1", job="a job", texts=("first",)),
                )

            assert write_stories_response == relays.WriteStoriesResponse(texts=("first", "second"))
            assert keep_drafted_stories_response == relays.KeepDraftedStoriesResponse(drafting_id="d1")
            assert fake_writing_application_client.jobs == ["a job"]
            assert fake_drafting_application_client.kept == [("d1", ("first",))]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
