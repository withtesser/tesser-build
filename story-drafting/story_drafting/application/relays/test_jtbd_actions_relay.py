from __future__ import annotations

import pytest

import story_drafting.application.relays as relays
import tesser.errors as errors


class TestInitializeJtbdRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        initialize_jtbd_request = relays.InitializeJtbdRequest(jtbd_id="jtbd-1", status="drafting")

        raw = relays.InitializeJtbdRequestSnapshot().serialize(initialize_jtbd_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "status": "drafting"}'

    def test_a_request_comes_back_equal(self) -> None:
        initialize_jtbd_request_snapshot = relays.InitializeJtbdRequestSnapshot()
        initialize_jtbd_request = relays.InitializeJtbdRequest(jtbd_id="jtbd-1", status="drafting")

        returned = initialize_jtbd_request_snapshot.deserialize(initialize_jtbd_request_snapshot.serialize(initialize_jtbd_request))

        assert returned == initialize_jtbd_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "status": "drafting"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.InitializeJtbdRequestSnapshot().deserialize(raw)


class TestInitializeJtbdResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.InitializeJtbdResponseSnapshot().serialize(relays.InitializeJtbdResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        initialize_jtbd_response_snapshot = relays.InitializeJtbdResponseSnapshot()
        initialize_jtbd_response = relays.InitializeJtbdResponse(jtbd_id="jtbd-1")

        returned = initialize_jtbd_response_snapshot.deserialize(
            initialize_jtbd_response_snapshot.serialize(initialize_jtbd_response)
        )

        assert returned == initialize_jtbd_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.InitializeJtbdResponseSnapshot().deserialize(raw)
