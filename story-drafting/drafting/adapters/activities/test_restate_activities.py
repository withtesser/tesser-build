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
import drafting.domain as domain


@ts.fake
class FakeRunApplicationClient(client.RunApplicationClient):

    def __init__(self) -> None:
        self.recorded: list[tuple[str, str]] = []

    async def record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        self.recorded.append((str(record_run_request.run.identity), str(record_run_request.run.job)))
        return relays.RecordRunResponse(run_id=str(record_run_request.run.identity))


class TestRestateRecordRun:

    async def test_restate_serves_record_run_and_a_call_made_with_its_handler_reaches_the_application_client(self) -> None:
        run_actions_service = restate.Service(f"RunActions{uuid.uuid4().hex}")
        fake_run_application_client = FakeRunApplicationClient()
        restate_record_run = activities.RestateRecordRun(run_actions_service, fake_run_application_client)
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

            run = domain.Run(domain.RunSpec(run_id="r1", job="ship", stage="drafting", stories=(), accepted_stories=()))
            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                record_run_response = await restate_client.Client(async_client).service_call(
                    restate_record_run.handler, relays.RecordRunRequest(run=run)
                )

            assert record_run_response == relays.RecordRunResponse(run_id="r1")
            assert fake_run_application_client.recorded == [("r1", "ship")]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)


@ts.fake
class FakeStoryApplicationClient(client.StoryApplicationClient):

    def __init__(self) -> None:
        self.jobs: list[str] = []

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        self.jobs.append(write_stories_request.job)
        return relays.WriteStoriesResponse(stories=("a story", "another story"))


class TestRestateWriteStories:

    async def test_restate_serves_write_stories_and_a_call_made_with_its_handler_reaches_the_application_client(self) -> None:
        story_actions_service = restate.Service(f"StoryActions{uuid.uuid4().hex}")
        fake_story_application_client = FakeStoryApplicationClient()
        restate_write_stories = activities.RestateWriteStories(story_actions_service, fake_story_application_client)
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
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([story_actions_service])),
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
                    restate_write_stories.handler, relays.WriteStoriesRequest(job="ship")
                )

            assert write_stories_response == relays.WriteStoriesResponse(stories=("a story", "another story"))
            assert fake_story_application_client.jobs == ["ship"]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
