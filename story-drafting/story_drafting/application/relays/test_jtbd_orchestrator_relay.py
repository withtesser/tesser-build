from __future__ import annotations

import pytest

import story_drafting.application.relays as relays
import tesser.errors as errors


class TestConductDraftingRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        conduct_drafting_request = relays.ConductDraftingRequest(jtbd_id="jtbd-1", status="drafting")

        raw = relays.ConductDraftingRequestSnapshot().serialize(conduct_drafting_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "status": "drafting"}'

    def test_a_request_comes_back_equal(self) -> None:
        conduct_drafting_request_snapshot = relays.ConductDraftingRequestSnapshot()
        conduct_drafting_request = relays.ConductDraftingRequest(jtbd_id="jtbd-1", status="drafting")

        returned = conduct_drafting_request_snapshot.deserialize(conduct_drafting_request_snapshot.serialize(conduct_drafting_request))

        assert returned == conduct_drafting_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "status": "drafting"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.ConductDraftingRequestSnapshot().deserialize(raw)


class TestConductDraftingResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.ConductDraftingResponseSnapshot().serialize(relays.ConductDraftingResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        conduct_drafting_response_snapshot = relays.ConductDraftingResponseSnapshot()
        conduct_drafting_response = relays.ConductDraftingResponse(jtbd_id="jtbd-1")

        returned = conduct_drafting_response_snapshot.deserialize(
            conduct_drafting_response_snapshot.serialize(conduct_drafting_response)
        )

        assert returned == conduct_drafting_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.ConductDraftingResponseSnapshot().deserialize(raw)
