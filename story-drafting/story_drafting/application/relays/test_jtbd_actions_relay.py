from __future__ import annotations

import pytest

import story_drafting.application.relays as relays
import tesser.errors as errors


class TestBeginDraftingRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        begin_drafting_request = relays.BeginDraftingRequest(jtbd_id="jtbd-1", status="drafting")

        raw = relays.BeginDraftingRequestSnapshot().serialize(begin_drafting_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "status": "drafting"}'

    def test_a_request_comes_back_equal(self) -> None:
        begin_drafting_request_snapshot = relays.BeginDraftingRequestSnapshot()
        begin_drafting_request = relays.BeginDraftingRequest(jtbd_id="jtbd-1", status="drafting")

        returned = begin_drafting_request_snapshot.deserialize(begin_drafting_request_snapshot.serialize(begin_drafting_request))

        assert returned == begin_drafting_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "status": "drafting"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.BeginDraftingRequestSnapshot().deserialize(raw)


class TestBeginDraftingResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.BeginDraftingResponseSnapshot().serialize(relays.BeginDraftingResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        begin_drafting_response_snapshot = relays.BeginDraftingResponseSnapshot()
        begin_drafting_response = relays.BeginDraftingResponse(jtbd_id="jtbd-1")

        returned = begin_drafting_response_snapshot.deserialize(
            begin_drafting_response_snapshot.serialize(begin_drafting_response)
        )

        assert returned == begin_drafting_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.BeginDraftingResponseSnapshot().deserialize(raw)
