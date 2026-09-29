from __future__ import annotations

import os

import tesser.testing as ts

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

    async def test_a_cli_add_reaches_the_wired_service(self) -> None:
        alpha = component.Alpha(component.Config(component.Spec(storage=os.environ["ALPHA_STORAGE"], ingress="http://localhost:8080")), FakeBetaCheck())
        cli_response = await handlers.Handler(alpha.client).add_part(protocol.CliRequest(args=("a", "p")))
        assert cli_response.line.text == "a"

    async def test_a_widget_beta_holds_a_key_for_stands_as_kept_and_one_it_holds_none_for_as_released(self) -> None:
        alpha = component.Alpha(component.Config(component.Spec(storage=os.environ["ALPHA_STORAGE"], ingress="http://localhost:8080")), FakeKeyedBetaCheck(frozenset({"k"})))
        kept = await alpha.client.add_part(client.AddPartRequest(name="k", part="k"))
        released = await alpha.client.add_part(client.AddPartRequest(name="z", part="z"))
        assert (kept.standing, released.standing) == ("kept", "released")
