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

    def __init__(self) -> None:
        self.jobs: list[str] = []

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        self.jobs.append(write_stories_request.job)
        return relays.WriteStoriesResponse(stories=("a story", "another story"))


class TestRestateRunActions:

    async def test_restate_serves_the_run_actions_and_a_call_made_with_each_handler_reaches_the_application_client(self) -> None:
        run_actions_service = restate.Service(f"RunActions{uuid.uuid4().hex}")
        fake_run_application_client = FakeRunApplicationClient()
        restate_keep_run = activities.RestateKeepRun(run_actions_service, fake_run_application_client)
        restate_offer_stories = activities.RestateOfferStories(run_actions_service, fake_run_application_client)
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
                keep_run_response = await restate_client.Client(async_client).service_call(
                    restate_keep_run.handler, relays.KeepRunRequest(run_id="r1", job="a job")
                )
                offer_stories_response = await restate_client.Client(async_client).service_call(
                    restate_offer_stories.handler,
                    relays.OfferStoriesRequest(run_id="r1", job="a job", stories=("a story",)),
                )

            assert keep_run_response == relays.KeepRunResponse(run_id="r1")
            assert fake_run_application_client.kept == [("r1", "a job")]
            assert offer_stories_response == relays.OfferStoriesResponse(run_id="r1")
            assert fake_run_application_client.offered == [("r1", ("a story",))]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)


class TestRestateWriteStories:

    async def test_restate_serves_write_stories_and_a_call_made_with_its_handler_reaches_the_application_client(self) -> None:
        drafter_actions_service = restate.Service(f"DrafterActions{uuid.uuid4().hex}")
        fake_drafter_application_client = FakeDrafterApplicationClient()
        restate_write_stories = activities.RestateWriteStories(drafter_actions_service, fake_drafter_application_client)
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([drafter_actions_service])),
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

            assert write_stories_response == relays.WriteStoriesResponse(stories=("a story", "another story"))
            assert fake_drafter_application_client.jobs == ["a job"]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
