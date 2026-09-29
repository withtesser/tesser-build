from __future__ import annotations

import pytest

import jtbds.application.relays as relays
import tesser.errors as errors


class TestDraftJtbdRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        draft_jtbd_request = relays.DraftJtbdRequest(jtbd_id="jtbd-1", description="design the dashboard", status="drafting")

        raw = relays.DraftJtbdRequestSnapshot().serialize(draft_jtbd_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "description": "design the dashboard", "status": "drafting"}'

    def test_a_request_comes_back_equal(self) -> None:
        draft_jtbd_request_snapshot = relays.DraftJtbdRequestSnapshot()
        draft_jtbd_request = relays.DraftJtbdRequest(jtbd_id="jtbd-1", description="design the dashboard", status="drafting")

        returned = draft_jtbd_request_snapshot.deserialize(draft_jtbd_request_snapshot.serialize(draft_jtbd_request))

        assert returned == draft_jtbd_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "description": "design the dashboard", "status": "drafting"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.DraftJtbdRequestSnapshot().deserialize(raw)


class TestDraftJtbdResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.DraftJtbdResponseSnapshot().serialize(relays.DraftJtbdResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        draft_jtbd_response_snapshot = relays.DraftJtbdResponseSnapshot()
        draft_jtbd_response = relays.DraftJtbdResponse(jtbd_id="jtbd-1")

        returned = draft_jtbd_response_snapshot.deserialize(
            draft_jtbd_response_snapshot.serialize(draft_jtbd_response)
        )

        assert returned == draft_jtbd_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.DraftJtbdResponseSnapshot().deserialize(raw)
