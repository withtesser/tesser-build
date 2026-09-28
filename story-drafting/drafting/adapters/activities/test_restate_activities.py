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

    def __init__(self) -> None:
        self.written: list[relays.WriteStoriesRequest] = []

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        self.written.append(write_stories_request)
        return relays.WriteStoriesResponse(stories=("As a developer, I want " + write_stories_request.job,))


class TestRestateRecordRun:

    async def test_restate_serves_record_run_and_a_call_made_with_its_handler_reaches_the_application_client(self) -> None:
        workflow_key = str(uuid.uuid4())
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
                    json={"uri": f"http://{os.environ['RESTATE_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                record_run_response = await restate_client.Client(async_client).service_call(
                    restate_record_run.handler, relays.RecordRunRequest(run_id=workflow_key, job="plan a migration", stage="drafting", stories=(), accepted_stories=())
                )

            assert record_run_response == relays.RecordRunResponse(run_id=workflow_key)
            assert [recorded.run_id for recorded in fake_run_application_client.recorded] == [workflow_key]
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
        story_writing_actions_service = restate.Service(f"StoryWritingActions{uuid.uuid4().hex}")
        fake_story_writing_application_client = FakeStoryWritingApplicationClient()
        restate_write_stories = activities.RestateWriteStories(
            story_writing_actions_service, fake_story_writing_application_client
        )
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([story_writing_actions_service])),
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
                write_stories_response = await restate_client.Client(async_client).service_call(
                    restate_write_stories.handler, relays.WriteStoriesRequest(job="plan a migration")
                )

            assert write_stories_response == relays.WriteStoriesResponse(
                stories=("As a developer, I want plan a migration",)
            )
            assert [written.job for written in fake_story_writing_application_client.written] == ["plan a migration"]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)


class TestRestateEngineRefusals:

    async def test_a_body_the_snapshot_cannot_read_is_a_terminal_500_that_is_not_retried(self) -> None:
        run_actions_service = restate.Service(f"RunActions{uuid.uuid4().hex}")
        restate_record_run = activities.RestateRecordRun(run_actions_service, FakeRunApplicationClient())
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
                    json={"uri": f"http://{os.environ['RESTATE_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                with pytest.raises(restate.HttpError) as refused:
                    await restate_client.Client(async_client).generic_call(
                        run_actions_service.name, restate_record_run.handler.__name__,
                        b"[1, 2]",
                        headers={"content-type": "application/json"},
                    )

            assert refused.value.status_code == 500
            assert json.loads(refused.value.body or "")["message"].startswith("Unable to parse an input argument.")
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)

    async def test_the_ingress_refuses_a_call_to_an_ingress_private_actions_service(self) -> None:
        run_actions_service = restate.Service(f"RunActions{uuid.uuid4().hex}", ingress_private=True)
        restate_record_run = activities.RestateRecordRun(run_actions_service, FakeRunApplicationClient())
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
                    json={"uri": f"http://{os.environ['RESTATE_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                with pytest.raises(restate.HttpError) as refused:
                    await restate_client.Client(async_client).service_call(restate_record_run.handler, relays.RecordRunRequest(run_id="run-1", job="plan a migration", stage="drafting", stories=(), accepted_stories=()))

            assert refused.value.status_code == 400
            assert json.loads(refused.value.body or "")["message"] == "the invoked service is not public"
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
