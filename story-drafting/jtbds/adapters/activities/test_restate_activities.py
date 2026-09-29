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

import jtbds.adapters.activities as activities
import jtbds.application.client as client
import jtbds.application.relays as relays


@ts.fake
class FakeJobToBeDoneApplicationClient(client.JobToBeDoneApplicationClient):

    def __init__(self) -> None:
        self.recorded: list[relays.InitializeJtbdRequest] = []

    async def initialize_jtbd(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> relays.InitializeJtbdResponse:
        self.recorded.append(initialize_jtbd_request)
        return relays.InitializeJtbdResponse(jtbd_id=initialize_jtbd_request.jtbd_id)


class TestRestateInitializeJtbd:

    async def test_restate_serves_initialize_jtbd_and_a_call_made_with_its_handler_reaches_the_application_client(self) -> None:
        workflow_key = str(uuid.uuid4())
        job_to_be_done_actions_service = restate.Service(f"JobToBeDoneActions{uuid.uuid4().hex}")
        fake_job_to_be_done_application_client = FakeJobToBeDoneApplicationClient()
        restate_initialize_jtbd = activities.RestateInitializeJtbd(job_to_be_done_actions_service, fake_job_to_be_done_application_client)
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([job_to_be_done_actions_service])),
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
                initialize_jtbd_response = await restate_client.Client(async_client).service_call(
                    restate_initialize_jtbd.handler, relays.InitializeJtbdRequest(jtbd_id=workflow_key, description="design new feature", status="drafting")
                )

            assert initialize_jtbd_response == relays.InitializeJtbdResponse(jtbd_id=workflow_key)
            assert [recorded.jtbd_id for recorded in fake_job_to_be_done_application_client.recorded] == [workflow_key]
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
        job_to_be_done_actions_service = restate.Service(f"JobToBeDoneActions{uuid.uuid4().hex}")
        restate_initialize_jtbd = activities.RestateInitializeJtbd(job_to_be_done_actions_service, FakeJobToBeDoneApplicationClient())
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([job_to_be_done_actions_service])),
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
                        job_to_be_done_actions_service.name, restate_initialize_jtbd.handler.__name__,
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
        job_to_be_done_actions_service = restate.Service(f"JobToBeDoneActions{uuid.uuid4().hex}", ingress_private=True)
        restate_initialize_jtbd = activities.RestateInitializeJtbd(job_to_be_done_actions_service, FakeJobToBeDoneApplicationClient())
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([job_to_be_done_actions_service])),
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
                    await restate_client.Client(async_client).service_call(restate_initialize_jtbd.handler, relays.InitializeJtbdRequest(jtbd_id="jtbd-1", description="design new feature", status="drafting"))

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
