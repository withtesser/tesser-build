from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestRecordJtbdRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        record_jtbd_request = relays.RecordJtbdRequest(jtbd_id="jtbd-1", situation="I am working through a multi-step piece of work with an agent", motivation="the steps and my checkpoints fixed in advance", outcome="I can step away and resume where we were")

        raw = relays.RecordJtbdRequestSnapshot().serialize(record_jtbd_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "situation": "I am working through a multi-step piece of work with an agent", "motivation": "the steps and my checkpoints fixed in advance", "outcome": "I can step away and resume where we were"}'

    def test_a_request_comes_back_equal(self) -> None:
        record_jtbd_request_snapshot = relays.RecordJtbdRequestSnapshot()
        record_jtbd_request = relays.RecordJtbdRequest(jtbd_id="jtbd-1", situation="I am working through a multi-step piece of work with an agent", motivation="the steps and my checkpoints fixed in advance", outcome="I can step away and resume where we were")

        returned = record_jtbd_request_snapshot.deserialize(record_jtbd_request_snapshot.serialize(record_jtbd_request))

        assert returned == record_jtbd_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "situation": "I am working through a multi-step piece of work with an agent", "motivation": "the steps and my checkpoints fixed in advance", "outcome": "I can step away and resume where we were"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.RecordJtbdRequestSnapshot().deserialize(raw)


class TestRecordJtbdResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.RecordJtbdResponseSnapshot().serialize(relays.RecordJtbdResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        record_jtbd_response_snapshot = relays.RecordJtbdResponseSnapshot()
        record_jtbd_response = relays.RecordJtbdResponse(jtbd_id="jtbd-1")

        returned = record_jtbd_response_snapshot.deserialize(
            record_jtbd_response_snapshot.serialize(record_jtbd_response)
        )

        assert returned == record_jtbd_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.RecordJtbdResponseSnapshot().deserialize(raw)
