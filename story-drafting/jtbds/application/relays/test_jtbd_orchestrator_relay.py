from __future__ import annotations

import pytest

import jtbds.application.relays as relays
import tesser.errors as errors


class TestProcessJtbdRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        process_jtbd_request = relays.ProcessJtbdRequest(jtbd_id="jtbd-1", description="design the dashboard", status="drafting")

        raw = relays.ProcessJtbdRequestSnapshot().serialize(process_jtbd_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "description": "design the dashboard", "status": "drafting"}'

    def test_a_request_comes_back_equal(self) -> None:
        process_jtbd_request_snapshot = relays.ProcessJtbdRequestSnapshot()
        process_jtbd_request = relays.ProcessJtbdRequest(jtbd_id="jtbd-1", description="design the dashboard", status="drafting")

        returned = process_jtbd_request_snapshot.deserialize(process_jtbd_request_snapshot.serialize(process_jtbd_request))

        assert returned == process_jtbd_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "description": "design the dashboard", "status": "drafting"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.ProcessJtbdRequestSnapshot().deserialize(raw)


class TestProcessJtbdResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.ProcessJtbdResponseSnapshot().serialize(relays.ProcessJtbdResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        process_jtbd_response_snapshot = relays.ProcessJtbdResponseSnapshot()
        process_jtbd_response = relays.ProcessJtbdResponse(jtbd_id="jtbd-1")

        returned = process_jtbd_response_snapshot.deserialize(
            process_jtbd_response_snapshot.serialize(process_jtbd_response)
        )

        assert returned == process_jtbd_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.ProcessJtbdResponseSnapshot().deserialize(raw)
