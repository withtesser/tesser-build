from __future__ import annotations

import tesser.testing as ts

import alpha.adapters.gateways as gateways
import alpha.application.ports as ports
import beta.client as beta_client


@ts.fake
class FakeBetaClient(beta_client.BetaClient):

    def check_key(self, check_key_request: beta_client.CheckKeyRequest) -> beta_client.CheckKeyResponse:
        return beta_client.CheckKeyResponse(held="no")


@ts.fake
class FakeHeldBetaClient(beta_client.BetaClient):

    def check_key(self, check_key_request: beta_client.CheckKeyRequest) -> beta_client.CheckKeyResponse:
        return beta_client.CheckKeyResponse(held="yes")


class TestBetaCheckGateway:

    def test_an_unheld_key_is_refused(self) -> None:
        beta_check_gateway = gateways.BetaCheckGateway(FakeBetaClient())
        check_name_response = beta_check_gateway.check_name(ports.CheckNameRequest(name="a"))
        assert check_name_response.outcome is ports.CheckNameOutcome.REFUSED

    def test_a_held_key_is_ok(self) -> None:
        beta_check_gateway = gateways.BetaCheckGateway(FakeHeldBetaClient())
        check_name_response = beta_check_gateway.check_name(ports.CheckNameRequest(name="k"))
        assert check_name_response.outcome is ports.CheckNameOutcome.OK
