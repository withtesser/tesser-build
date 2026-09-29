from __future__ import annotations

import pytest

import jtbd.application.relays as relays
import tesser.errors as errors


class TestMarkJtbdDraftingRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        mark_jtbd_drafting_request = relays.MarkJtbdDraftingRequest(jtbd_id="jtbd-1", description="design-feature", status="drafting")

        raw = relays.MarkJtbdDraftingRequestSnapshot().serialize(mark_jtbd_drafting_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "description": "design-feature", "status": "drafting"}'

    def test_a_request_comes_back_equal(self) -> None:
        mark_jtbd_drafting_request_snapshot = relays.MarkJtbdDraftingRequestSnapshot()
        mark_jtbd_drafting_request = relays.MarkJtbdDraftingRequest(jtbd_id="jtbd-1", description="design-feature", status="drafting")

        returned = mark_jtbd_drafting_request_snapshot.deserialize(mark_jtbd_drafting_request_snapshot.serialize(mark_jtbd_drafting_request))

        assert returned == mark_jtbd_drafting_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "description": "design-feature", "status": "drafting"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.MarkJtbdDraftingRequestSnapshot().deserialize(raw)


class TestMarkJtbdDraftingResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.MarkJtbdDraftingResponseSnapshot().serialize(relays.MarkJtbdDraftingResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        mark_jtbd_drafting_response_snapshot = relays.MarkJtbdDraftingResponseSnapshot()
        mark_jtbd_drafting_response = relays.MarkJtbdDraftingResponse(jtbd_id="jtbd-1")

        returned = mark_jtbd_drafting_response_snapshot.deserialize(
            mark_jtbd_drafting_response_snapshot.serialize(mark_jtbd_drafting_response)
        )

        assert returned == mark_jtbd_drafting_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.MarkJtbdDraftingResponseSnapshot().deserialize(raw)
