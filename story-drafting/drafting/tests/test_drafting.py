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

import drafting.adapters.handlers as handlers
import drafting.client as client
import drafting.component as component
import protocol as protocol


class TestDraftingContext:

    async def test_a_run_never_opened_is_not_found(self) -> None:
        drafting = component.Drafting(component.Config(component.Spec(engine_url="http://127.0.0.1:9", story_writer="canned", anthropic_api_key="")))
        try:
            with pytest.raises(client.RunNotFound):
                await drafting.client.get_run(client.GetRunRequest(run_id=str(uuid.uuid4())))
        finally:
            drafting.close()

    async def test_a_run_the_domain_refuses_is_rejected_through_the_handler(self) -> None:
        drafting = component.Drafting(component.Config(component.Spec(engine_url="http://127.0.0.1:9", story_writer="canned", anthropic_api_key="")))
        try:
            http_response = await handlers.Handler(drafting.client).open_run(
                protocol.HttpRequest(path_params={}, body=b'{"run_id": "r1", "job": ""}')
            )
        finally:
            drafting.close()
        assert http_response.status_code == 422

    async def test_an_opened_run_is_drafted_and_waits_for_the_pick_with_its_stories_and_none_accepted(self) -> None:
        drafting = component.Drafting(component.Config(component.Spec(engine_url=os.environ["RESTATE_URL"], story_writer="canned", anthropic_api_key="")))
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
                typing.cast(
                    hypercorn_typing.ASGIFramework,
                    restate.app(
                        [drafting.run_actions_service, drafting.story_actions_service, drafting.run_orchestrator_workflow]
                    ),
                ),
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
            job = "keep a changelog " + uuid.uuid4().hex
            open_run_response = await drafting.client.open_run(client.OpenRunRequest(run_id=run_id, job=job))
            get_run_response: client.GetRunResponse | None = None
            for _ in range(200):
                try:
                    get_run_response = await drafting.client.get_run(client.GetRunRequest(run_id=run_id))
                except client.RunNotFound:
                    get_run_response = None
                if get_run_response is not None and get_run_response.stage == "awaiting_pick":
                    break
                await asyncio.sleep(0.05)
            running = await admin.post(
                "/query",
                headers={"accept": "application/json"},
                json={
                    "query": "SELECT id FROM sys_invocation "
                    f"WHERE target_service_name = 'RunOrchestrator' AND target_service_key = '{run_id}'"
                },
            )
            for row in running.json()["rows"]:
                await admin.patch(f"/invocations/{row['id']}/kill")

            assert open_run_response.run_id == run_id
            assert get_run_response is not None
            assert (get_run_response.run_id, get_run_response.job) == (run_id, job)
            assert get_run_response.stage == "awaiting_pick"
            assert get_run_response.stories
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
