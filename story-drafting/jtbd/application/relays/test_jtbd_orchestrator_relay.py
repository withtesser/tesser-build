from __future__ import annotations

import pytest

import jtbd.application.relays as relays
import tesser.errors as errors


class TestDraftForJtbdRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        draft_for_jtbd_request = relays.DraftForJtbdRequest(jtbd_id="jtbd-1", description="design-feature", status="drafting")

        raw = relays.DraftForJtbdRequestSnapshot().serialize(draft_for_jtbd_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "description": "design-feature", "status": "drafting"}'

    def test_a_request_comes_back_equal(self) -> None:
        draft_for_jtbd_request_snapshot = relays.DraftForJtbdRequestSnapshot()
        draft_for_jtbd_request = relays.DraftForJtbdRequest(jtbd_id="jtbd-1", description="design-feature", status="drafting")

        returned = draft_for_jtbd_request_snapshot.deserialize(draft_for_jtbd_request_snapshot.serialize(draft_for_jtbd_request))

        assert returned == draft_for_jtbd_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "description": "design-feature", "status": "drafting"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.DraftForJtbdRequestSnapshot().deserialize(raw)


class TestDraftForJtbdResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.DraftForJtbdResponseSnapshot().serialize(relays.DraftForJtbdResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        draft_for_jtbd_response_snapshot = relays.DraftForJtbdResponseSnapshot()
        draft_for_jtbd_response = relays.DraftForJtbdResponse(jtbd_id="jtbd-1")

        returned = draft_for_jtbd_response_snapshot.deserialize(
            draft_for_jtbd_response_snapshot.serialize(draft_for_jtbd_response)
        )

        assert returned == draft_for_jtbd_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.DraftForJtbdResponseSnapshot().deserialize(raw)
