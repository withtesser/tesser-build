from __future__ import annotations

import pytest

import story_drafting.application.relays as relays
import tesser.errors as errors


class TestWriteDraftsRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        write_drafts_request = relays.WriteDraftsRequest(jtbd_id="jtbd-1", job="Design a feature, get my sign-off, then build it")

        raw = relays.WriteDraftsRequestSnapshot().serialize(write_drafts_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "job": "Design a feature, get my sign-off, then build it"}'

    def test_a_request_comes_back_equal(self) -> None:
        write_drafts_request_snapshot = relays.WriteDraftsRequestSnapshot()
        write_drafts_request = relays.WriteDraftsRequest(jtbd_id="jtbd-1", job="Design a feature, get my sign-off, then build it")

        returned = write_drafts_request_snapshot.deserialize(write_drafts_request_snapshot.serialize(write_drafts_request))

        assert returned == write_drafts_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "job": "Design a feature, get my sign-off, then build it"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.WriteDraftsRequestSnapshot().deserialize(raw)


class TestWriteDraftsResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.WriteDraftsResponseSnapshot().serialize(relays.WriteDraftsResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        write_drafts_response_snapshot = relays.WriteDraftsResponseSnapshot()
        write_drafts_response = relays.WriteDraftsResponse(jtbd_id="jtbd-1")

        returned = write_drafts_response_snapshot.deserialize(
            write_drafts_response_snapshot.serialize(write_drafts_response)
        )

        assert returned == write_drafts_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.WriteDraftsResponseSnapshot().deserialize(raw)
