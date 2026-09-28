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
import restate.client as restate_client

import drafting.adapters.workflows as workflows
import drafting.application.relays as relays


class TestRestateConductRun:

    async def test_conduct_run_answers_the_run_its_key_names_and_refuses_a_run_it_does_not(self) -> None:
        run_id = str(uuid.uuid4())
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{uuid.uuid4().hex}")
        restate_conduct_run = workflows.RestateConductRun(run_orchestrator_workflow)
        with socket.socket() as probe:
            probe.bind(("0.0.0.0", 0))
            port = probe.getsockname()[1]
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(hypercorn_typing.ASGIFramework, restate.app([run_orchestrator_workflow])),
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
                conduct_run_response = await restate_client.Client(async_client).workflow_call(
                    restate_conduct_run.handler, key=run_id, arg=relays.ConductRunRequest(run_id=run_id, job="ship it")
                )
                with pytest.raises(restate.HttpError) as foreign:
                    await restate_client.Client(async_client).workflow_call(
                        restate_conduct_run.handler,
                        key="other-" + run_id,
                        arg=relays.ConductRunRequest(run_id=run_id, job="ship it"),
                    )

            assert conduct_run_response == relays.ConductRunResponse(run_id=run_id)
            assert foreign.value.status_code == 400
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
