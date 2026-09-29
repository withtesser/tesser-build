from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestRecordSubmissionRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        record_submission_request = relays.RecordSubmissionRequest(jtbd_id="jtbd-1", job="design a checkout then build it")

        raw = relays.RecordSubmissionRequestSnapshot().serialize(record_submission_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "job": "design a checkout then build it"}'

    def test_a_request_comes_back_equal(self) -> None:
        record_submission_request_snapshot = relays.RecordSubmissionRequestSnapshot()
        record_submission_request = relays.RecordSubmissionRequest(jtbd_id="jtbd-1", job="design a checkout then build it")

        returned = record_submission_request_snapshot.deserialize(record_submission_request_snapshot.serialize(record_submission_request))

        assert returned == record_submission_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"jtbd_id": 1, "job": "design a checkout then build it"}',
            b'["jtbd-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.RecordSubmissionRequestSnapshot().deserialize(raw)


class TestRecordSubmissionResponseSnapshot:

    def test_a_response_is_its_jtbd_id(self) -> None:
        raw = relays.RecordSubmissionResponseSnapshot().serialize(relays.RecordSubmissionResponse(jtbd_id="jtbd-1"))

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        record_submission_response_snapshot = relays.RecordSubmissionResponseSnapshot()
        record_submission_response = relays.RecordSubmissionResponse(jtbd_id="jtbd-1")

        returned = record_submission_response_snapshot.deserialize(
            record_submission_response_snapshot.serialize(record_submission_response)
        )

        assert returned == record_submission_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"jtbd_id": 1}', b'["jtbd-1"]'):
            with pytest.raises(errors.DomainError):
                relays.RecordSubmissionResponseSnapshot().deserialize(raw)
