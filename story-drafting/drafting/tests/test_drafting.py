from __future__ import annotations

import asyncio
import os
import socket
import typing
import uuid

import httpx
import hypercorn.asyncio as hypercorn_asyncio
import hypercorn.config as hypercorn_config
import hypercorn.typing as hypercorn_typing
import pytest
import restate

import drafting.client as client
import drafting.component as component


class TestDraftingContext:

    async def test_a_run_the_domain_refuses_is_the_situation_of_that_name(self) -> None:
        drafting = component.Drafting(component.Config(component.Spec(ingress="http://127.0.0.1:9")))
        try:
            with pytest.raises(client.RunRejected):
                await drafting.client.begin_run(client.BeginRunRequest(run_id="r1", job=""))
        finally:
            drafting.close()

    async def test_a_run_never_begun_is_not_found(self) -> None:
        drafting = component.Drafting(component.Config(component.Spec(ingress="http://127.0.0.1:9")))
        try:
            with pytest.raises(client.RunNotFound):
                await drafting.client.get_run(client.GetRunRequest(run_id=str(uuid.uuid4())))
        finally:
            drafting.close()


class TestDraftingThroughTheEngine:

    async def test_a_begun_run_is_read_back_with_its_job(self) -> None:
        drafting = component.Drafting(component.Config(component.Spec(ingress=os.environ["RESTATE_INGRESS"])))
        containers: list[restate.Service | restate.Workflow] = [
            drafting.run_actions_service,
            drafting.run_orchestrator_workflow,
        ]
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app(containers)),
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

            run_id = str(uuid.uuid4())
            begin_run_response = await drafting.client.begin_run(client.BeginRunRequest(run_id=run_id, job="a job"))
            get_run_response: client.GetRunResponse | None = None
            for _ in range(100):
                try:
                    get_run_response = await drafting.client.get_run(client.GetRunRequest(run_id=run_id))
                    break
                except client.RunNotFound:
                    await asyncio.sleep(0.05)

            assert begin_run_response.run_id == run_id
            assert get_run_response is not None
            assert (get_run_response.run_id, get_run_response.job) == (run_id, "a job")
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
            drafting.close()
