from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestRecordRunRequestSnapshot:

    def test_a_request_is_the_whole_run(self) -> None:
        raw = relays.RecordRunRequestSnapshot().serialize(
            relays.RecordRunRequest(
                run_id="r1",
                job="ship it",
                step="awaiting_pick",
                drafted_stories=("first",),
                accepted_stories=(),
            )
        )

        assert raw == (
            b'{"run_id": "r1", "job": "ship it", "step": "awaiting_pick", '
            b'"drafted_stories": ["first"], "accepted_stories": []}'
        )

    def test_a_request_comes_back_equal(self) -> None:
        record_run_request_snapshot = relays.RecordRunRequestSnapshot()
        record_run_request = relays.RecordRunRequest(
            run_id="r1",
            job="ship it",
            step="awaiting_pick",
            drafted_stories=("first",),
            accepted_stories=(),
        )

        returned = record_run_request_snapshot.deserialize(record_run_request_snapshot.serialize(record_run_request))

        assert returned == record_run_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"run_id": "r1", "job": "ship it", "step": "drafting", "drafted_stories": []}',
            b'{"run_id": "r1", "job": "ship it", "step": 1, "drafted_stories": [], "accepted_stories": []}',
            b'{"run_id": "r1", "job": "ship it", "step": "drafting", "drafted_stories": [1], "accepted_stories": []}',
            b'["r1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.RecordRunRequestSnapshot().deserialize(raw)


class TestRecordRunResponseSnapshot:

    def test_a_response_is_its_run_id(self) -> None:
        raw = relays.RecordRunResponseSnapshot().serialize(relays.RecordRunResponse(run_id="r1"))

        assert raw == b'{"run_id": "r1"}'

    def test_a_response_comes_back_equal(self) -> None:
        record_run_response_snapshot = relays.RecordRunResponseSnapshot()
        record_run_response = relays.RecordRunResponse(run_id="r1")

        returned = record_run_response_snapshot.deserialize(record_run_response_snapshot.serialize(record_run_response))

        assert returned == record_run_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"run_id": 1}', b'["r1"]'):
            with pytest.raises(errors.DomainError):
                relays.RecordRunResponseSnapshot().deserialize(raw)
