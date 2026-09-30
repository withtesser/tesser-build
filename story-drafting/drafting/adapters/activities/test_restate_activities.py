# pragma: tesser-generated; regenerate from the composition, never edit by hand
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
class FakeJtbdApplicationClient(client.JtbdApplicationClient):

    def __init__(self) -> None:
        self.received: list[relays.DraftStoriesRequest] = []

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        self.received.append(draft_stories_request)
        return relays.DraftStoriesResponse(jtbd_id=draft_stories_request.jtbd_id)


class TestRestateDraftStories:

    async def test_restate_serves_draft_stories_and_a_call_made_with_its_handler_reaches_the_application_client(self) -> None:
        jtbd_actions_service = restate.Service(f"JtbdActions{uuid.uuid4().hex}")
        fake_jtbd_application_client = FakeJtbdApplicationClient()
        restate_draft_stories = activities.RestateDraftStories(jtbd_actions_service, fake_jtbd_application_client)
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([jtbd_actions_service])),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        admin = httpx.AsyncClient(base_url=os.environ["RESTATE_ADMIN"], timeout=10.0)
        registered = httpx.Response(503)
        try:
            registering_until = asyncio.get_running_loop().time() + 30.0
            while True:
                registered = await admin.post(
                    "/deployments",
                    json={"uri": f"http://{os.environ['RESTATE_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success or asyncio.get_running_loop().time() > registering_until:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                draft_stories_response = await restate_client.Client(async_client).service_call(
                    restate_draft_stories.handler, relays.DraftStoriesRequest(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away")
                )

            assert draft_stories_response == relays.DraftStoriesResponse(jtbd_id="jtbd-1")
            assert fake_jtbd_application_client.received == [relays.DraftStoriesRequest(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away")]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.wait_for(asyncio.gather(serving, return_exceptions=True), timeout=5.0)


class TestRestateEngineRefusals:

    async def test_a_body_the_snapshot_cannot_read_is_a_terminal_500_that_is_not_retried(self) -> None:
        jtbd_actions_service = restate.Service(f"JtbdActions{uuid.uuid4().hex}")
        restate_draft_stories = activities.RestateDraftStories(jtbd_actions_service, FakeJtbdApplicationClient())
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([jtbd_actions_service])),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        admin = httpx.AsyncClient(base_url=os.environ["RESTATE_ADMIN"], timeout=10.0)
        registered = httpx.Response(503)
        try:
            registering_until = asyncio.get_running_loop().time() + 30.0
            while True:
                registered = await admin.post(
                    "/deployments",
                    json={"uri": f"http://{os.environ['RESTATE_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success or asyncio.get_running_loop().time() > registering_until:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                with pytest.raises(restate.HttpError) as refused:
                    await restate_client.Client(async_client).generic_call(
                        jtbd_actions_service.name, restate_draft_stories.handler.__name__,
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
            await asyncio.wait_for(asyncio.gather(serving, return_exceptions=True), timeout=5.0)

    async def test_the_ingress_refuses_a_call_to_an_ingress_private_actions_service(self) -> None:
        jtbd_actions_service = restate.Service(f"JtbdActions{uuid.uuid4().hex}", ingress_private=True)
        restate_draft_stories = activities.RestateDraftStories(jtbd_actions_service, FakeJtbdApplicationClient())
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([jtbd_actions_service])),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        admin = httpx.AsyncClient(base_url=os.environ["RESTATE_ADMIN"], timeout=10.0)
        registered = httpx.Response(503)
        try:
            registering_until = asyncio.get_running_loop().time() + 30.0
            while True:
                registered = await admin.post(
                    "/deployments",
                    json={"uri": f"http://{os.environ['RESTATE_CALLBACK_HOST']}:{port}", "force": True},
                )
                if registered.is_success or asyncio.get_running_loop().time() > registering_until:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            async with httpx.AsyncClient(base_url=os.environ["RESTATE_INGRESS"], timeout=30.0) as async_client:
                with pytest.raises(restate.HttpError) as refused:
                    await restate_client.Client(async_client).service_call(
                        restate_draft_stories.handler, relays.DraftStoriesRequest(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away")
                    )

            assert refused.value.status_code == 400
            assert json.loads(refused.value.body or "")["message"] == "the invoked service is not public"
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.wait_for(asyncio.gather(serving, return_exceptions=True), timeout=5.0)
