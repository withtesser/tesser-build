from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestArrangeDraftingRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        arrange_drafting_request = relays.ArrangeDraftingRequest(jtbd_id="jtbd-1", status="pending")

        raw = relays.ArrangeDraftingRequestSnapshot().serialize(arrange_drafting_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "status": "pending"}'

    def test_a_request_comes_back_equal(self) -> None:
        arrange_drafting_request_snapshot = relays.ArrangeDraftingRequestSnapshot()
        arrange_drafting_request = relays.ArrangeDraftingRequest(jtbd_id="jtbd-1", status="pending")

        returned = arrange_drafting_request_snapshot.deserialize(arrange_drafting_request_snapshot.serialize(arrange_drafting_request))

        assert returned == arrange_drafting_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "status": "pending"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.ArrangeDraftingRequestSnapshot().deserialize(raw)


class TestArrangeDraftingResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.ArrangeDraftingResponseSnapshot().serialize(relays.ArrangeDraftingResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        arrange_drafting_response_snapshot = relays.ArrangeDraftingResponseSnapshot()
        arrange_drafting_response = relays.ArrangeDraftingResponse(jtbd_id="jtbd-1")

        returned = arrange_drafting_response_snapshot.deserialize(
            arrange_drafting_response_snapshot.serialize(arrange_drafting_response)
        )

        assert returned == arrange_drafting_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.ArrangeDraftingResponseSnapshot().deserialize(raw)
