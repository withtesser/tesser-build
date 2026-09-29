from __future__ import annotations

import pytest

import drafting.application.relays as relays
import drafting.domain as domain
import tesser.errors as errors


class TestRecordRunRequestSnapshot:

    def test_a_record_run_request_carries_its_run_across(self) -> None:
        run = domain.Run(domain.RunSpec(run_id="r1", job="ship", stage="drafting", stories=(), accepted_stories=()))
        record_run_request = relays.RecordRunRequestSnapshot().deserialize(
            relays.RecordRunRequestSnapshot().serialize(relays.RecordRunRequest(run=run))
        )
        assert record_run_request.run.identity == run.identity
        assert record_run_request.run.stage == run.stage


class TestRecordRunResponseSnapshot:

    def test_a_record_run_response_round_trips(self) -> None:
        record_run_response = relays.RecordRunResponse(run_id="r1")
        assert (
            relays.RecordRunResponseSnapshot().deserialize(relays.RecordRunResponseSnapshot().serialize(record_run_response))
            == record_run_response
        )

    def test_a_record_run_response_without_a_run_id_is_invalid(self) -> None:
        with pytest.raises(errors.DomainError):
            relays.RecordRunResponseSnapshot().deserialize(b"{}")
