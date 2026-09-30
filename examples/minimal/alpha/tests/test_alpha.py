from __future__ import annotations

import asyncio
import typing
import uuid

import tesser.testing as ts
import httpx
import hypercorn.asyncio as hypercorn_asyncio
import hypercorn.config as hypercorn_config
import hypercorn.typing as hypercorn_typing
import restate

import alpha.adapters.handlers as handlers
import alpha.application.ports as ports
import alpha.client as client
import alpha.component as component
import protocol


@ts.fake
class FakeBetaCheck(ports.BetaCheck):

    def check_name(self, check_name_request: ports.CheckNameRequest) -> ports.CheckNameResponse:
        return ports.CheckNameResponse(outcome=ports.CheckNameOutcome.OK)


@ts.fake
class FakeKeyedBetaCheck(ports.BetaCheck):

    def __init__(self, held: frozenset[str]) -> None:
        self._held = held

    def check_name(self, check_name_request: ports.CheckNameRequest) -> ports.CheckNameResponse:
        if check_name_request.name in self._held:
            return ports.CheckNameResponse(outcome=ports.CheckNameOutcome.OK)
        return ports.CheckNameResponse(outcome=ports.CheckNameOutcome.REFUSED)


class TestAlphaContext:

    async def test_a_cli_add_reaches_the_wired_service(self, storage_url: str) -> None:
        alpha = component.Alpha(component.Config(component.Spec(storage=storage_url, engine_url="http://localhost:8080")), FakeBetaCheck())
        cli_response = await handlers.Handler(alpha.client).add_part(protocol.CliRequest(args=("a", "p")))
        assert cli_response.line.text == "a"

    async def test_a_widget_beta_holds_a_key_for_stands_as_kept_and_one_it_holds_none_for_as_released(self, storage_url: str) -> None:
        alpha = component.Alpha(component.Config(component.Spec(storage=storage_url, engine_url="http://localhost:8080")), FakeKeyedBetaCheck(frozenset({"k"})))
        kept = await alpha.client.add_part(client.AddPartRequest(name="k", part="k"))
        released = await alpha.client.add_part(client.AddPartRequest(name="z", part="z"))
        assert (kept.standing, released.standing) == ("kept", "released")

    async def test_a_created_widget_is_found_only_once_its_name_is_approved(self, storage_url: str, engine_url: str, engine_admin_url: str, engine_callback_host: str, free_port: int) -> None:
        name = "w-" + uuid.uuid4().hex
        alpha = component.Alpha(
            component.Config(component.Spec(storage=storage_url, engine_url=engine_url)),
            FakeBetaCheck(),
        )
        port = free_port
        hypercorn_config_config = hypercorn_config.Config()
        hypercorn_config_config.bind = [f"0.0.0.0:{port}"]
        shutdown = asyncio.Event()
        serving = asyncio.create_task(
            hypercorn_asyncio.serve(
                typing.cast(
                    hypercorn_typing.ASGIFramework,
                    restate.app([alpha.widget_actions_service, alpha.widget_orchestrator_workflow]),
                ),
                hypercorn_config_config,
                shutdown_trigger=shutdown.wait,
            )
        )
        admin = httpx.AsyncClient(base_url=engine_admin_url, timeout=10.0)
        registered = httpx.Response(503)
        try:
            for _ in range(50):
                registered = await admin.post(
                    "/deployments",
                    json={"uri": f"http://{engine_callback_host}:{port}", "force": True},
                )
                if registered.is_success:
                    break
                await asyncio.sleep(0.1)
            assert registered.is_success, registered.text

            create_widget_response = await alpha.client.create_widget(client.CreateWidgetRequest(name=name))
            found_before_approval = await alpha.client.find_widget(client.FindWidgetRequest(name=name))
            approved = ""
            for _ in range(100):
                try:
                    approved = (await alpha.client.approve_widget(client.ApproveWidgetRequest(name=name))).name
                    break
                except restate.HttpError as not_started:
                    if not_started.status_code != 412:
                        raise
                    await asyncio.sleep(0.05)
            found = found_before_approval
            for _ in range(100):
                found = await alpha.client.find_widget(client.FindWidgetRequest(name=name))
                if found.found == "yes":
                    break
                await asyncio.sleep(0.05)

            assert (create_widget_response.name, approved) == (name, name)
            assert (found_before_approval.found, found.found) == ("no", "yes")
        finally:
            if registered.is_success:
                await admin.delete(f"/deployments/{registered.json()['id']}", params={"force": "true"})
            await admin.aclose()
            shutdown.set()
            await asyncio.wait([serving], timeout=1.0)
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)
            alpha.close()
