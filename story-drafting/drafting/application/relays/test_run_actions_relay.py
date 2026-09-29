from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestRecordRunRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        record_run_request = relays.RecordRunRequest(run_id="run-1", job="Plan a trip")

        raw = relays.RecordRunRequestSnapshot().serialize(record_run_request)

        assert raw == b'{"run_id": "run-1", "job": "Plan a trip"}'

    def test_a_request_comes_back_equal(self) -> None:
        record_run_request_snapshot = relays.RecordRunRequestSnapshot()
        record_run_request = relays.RecordRunRequest(run_id="run-1", job="Plan a trip")

        returned = record_run_request_snapshot.deserialize(record_run_request_snapshot.serialize(record_run_request))

        assert returned == record_run_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"run_id": 1, "job": "Plan a trip"}',
            b'["run-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.RecordRunRequestSnapshot().deserialize(raw)


class TestRecordRunResponseSnapshot:

    def test_a_response_is_its_run_id(self) -> None:
        raw = relays.RecordRunResponseSnapshot().serialize(relays.RecordRunResponse(run_id="run-1"))

        assert raw == b'{"run_id": "run-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        record_run_response_snapshot = relays.RecordRunResponseSnapshot()
        record_run_response = relays.RecordRunResponse(run_id="run-1")

        returned = record_run_response_snapshot.deserialize(
            record_run_response_snapshot.serialize(record_run_response)
        )

        assert returned == record_run_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"run_id": 1}', b'["run-1"]'):
            with pytest.raises(errors.DomainError):
                relays.RecordRunResponseSnapshot().deserialize(raw)
