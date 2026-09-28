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
import restate

import drafting.adapters.dispatchers as dispatchers
import drafting.adapters.workflows as workflows
import drafting.application.relays as relays


class TestRestateHttpRunOrchestratorRelay:

    async def test_starting_a_run_sends_the_workflow_its_run_id_keys_and_answers_without_waiting(self) -> None:
        run_id = str(uuid.uuid4())
        suffix = uuid.uuid4().hex
        run_orchestrator_workflow = restate.Workflow(f"RunOrchestrator{suffix}")
        restate_http_run_orchestrator_relay = dispatchers.RestateHttpRunOrchestratorRelay(
            os.environ["RESTATE_INGRESS"], workflows.RestateConductRun(run_orchestrator_workflow)
        )
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

            start_conduct_run_response = await restate_http_run_orchestrator_relay.start_conduct_run(
                relays.ConductRunRequest(run_id=run_id, job="ship it")
            )
            statuses: list[str] = []
            for _ in range(100):
                queried = await admin.post(
                    "/query",
                    headers={"accept": "application/json"},
                    json={
                        "query": "SELECT status FROM sys_invocation "
                        f"WHERE target = 'RunOrchestrator{suffix}/{run_id}/conduct_run'"
                    },
                )
                statuses = [row["status"] for row in queried.json()["rows"]]
                if statuses == ["completed"]:
                    break
                await asyncio.sleep(0.05)

            assert start_conduct_run_response == relays.StartConductRunResponse(run_id=run_id)
            assert statuses == ["completed"]
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
