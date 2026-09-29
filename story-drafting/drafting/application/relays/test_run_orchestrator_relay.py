from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestConductRunRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        conduct_run_request = relays.ConductRunRequest(run_id="run-1", job="Plan a trip")

        raw = relays.ConductRunRequestSnapshot().serialize(conduct_run_request)

        assert raw == b'{"run_id": "run-1", "job": "Plan a trip"}'

    def test_a_request_comes_back_equal(self) -> None:
        conduct_run_request_snapshot = relays.ConductRunRequestSnapshot()
        conduct_run_request = relays.ConductRunRequest(run_id="run-1", job="Plan a trip")

        returned = conduct_run_request_snapshot.deserialize(conduct_run_request_snapshot.serialize(conduct_run_request))

        assert returned == conduct_run_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"run_id": 1, "job": "Plan a trip"}',
            b'["run-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.ConductRunRequestSnapshot().deserialize(raw)


class TestConductRunResponseSnapshot:

    def test_a_response_is_its_run_id(self) -> None:
        raw = relays.ConductRunResponseSnapshot().serialize(relays.ConductRunResponse(run_id="run-1"))

        assert raw == b'{"run_id": "run-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        conduct_run_response_snapshot = relays.ConductRunResponseSnapshot()
        conduct_run_response = relays.ConductRunResponse(run_id="run-1")

        returned = conduct_run_response_snapshot.deserialize(
            conduct_run_response_snapshot.serialize(conduct_run_response)
        )

        assert returned == conduct_run_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"run_id": 1}', b'["run-1"]'):
            with pytest.raises(errors.DomainError):
                relays.ConductRunResponseSnapshot().deserialize(raw)
