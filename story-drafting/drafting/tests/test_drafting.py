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
        drafting = component.Drafting(component.Config(component.Spec(ingress="http://127.0.0.1:9", drafter="canned", anthropic_api_key="")))
        try:
            with pytest.raises(client.RunRejected):
                await drafting.client.begin_run(client.BeginRunRequest(run_id="r1", job=""))
        finally:
            drafting.close()

    async def test_a_run_never_begun_is_not_found(self) -> None:
        drafting = component.Drafting(component.Config(component.Spec(ingress="http://127.0.0.1:9", drafter="canned", anthropic_api_key="")))
        try:
            with pytest.raises(client.RunNotFound):
                await drafting.client.get_run(client.GetRunRequest(run_id=str(uuid.uuid4())))
        finally:
            drafting.close()


class TestDraftingThroughTheEngine:

    async def test_a_begun_run_waits_for_the_pick_with_drafted_stories_and_none_accepted(self) -> None:
        drafting = component.Drafting(component.Config(component.Spec(ingress=os.environ["RESTATE_INGRESS"], drafter="canned", anthropic_api_key="")))
        containers: list[restate.Service | restate.Workflow] = [
            drafting.run_actions_service,
            drafting.drafter_actions_service,
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
                except client.RunNotFound:
                    get_run_response = None
                if get_run_response is not None and get_run_response.stage == "awaiting_pick":
                    break
                await asyncio.sleep(0.05)
            invoked = await admin.post(
                "/query",
                headers={"accept": "application/json"},
                json={
                    "query": "SELECT id FROM sys_invocation "
                    f"WHERE target_service_name = 'RunOrchestrator' AND target_service_key = '{run_id}'"
                },
            )
            for row in invoked.json()["rows"]:
                await admin.patch(f"/invocations/{row['id']}/kill")

            assert begin_run_response.run_id == run_id
            assert get_run_response is not None
            assert (get_run_response.run_id, get_run_response.job) == (run_id, "a job")
            assert get_run_response.stage == "awaiting_pick"
            assert get_run_response.stories != ()
            assert get_run_response.accepted_stories == ()
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
            drafting.close()
