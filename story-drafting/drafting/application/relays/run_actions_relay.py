from __future__ import annotations

import json
import typing

import tesser.application as ts

import drafting.application.snapshots as snapshots
import drafting.domain as domain
import tesser.errors as errors


class RecordRunRequest(ts.Request):

    def __init__(self, run: domain.Run) -> None:
        self.run = run


class RecordRunRequestSnapshot(ts.Serde):

    def serialize(self, record_run_request: RecordRunRequest) -> bytes:
        return snapshots.RunSnapshot().serialize(record_run_request.run)

    def deserialize(self, buf: bytes) -> RecordRunRequest:
        return RecordRunRequest(run=snapshots.RunSnapshot().deserialize(buf))


class RecordRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class RecordRunResponseSnapshot(ts.Serde):

    def serialize(self, record_run_response: RecordRunResponse) -> bytes:
        return json.dumps({"run_id": record_run_response.run_id}).encode()

    def deserialize(self, buf: bytes) -> RecordRunResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("run_id"), str)):
            raise errors.invalid("invalid_snapshot", "a record run response is a run_id")
        return RecordRunResponse(run_id=snapshot["run_id"])


class RunActionsRelay(ts.Relay, typing.Protocol):

    async def run_record_run(self, record_run_request: RecordRunRequest) -> RecordRunResponse: ...
