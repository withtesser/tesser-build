from __future__ import annotations

import json
import typing

import tesser.application as ts


class KeepRunRequest(ts.Request):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class KeepRunRequestSnapshot(ts.Serde):

    def serialize(self, keep_run_request: KeepRunRequest) -> bytes:
        return json.dumps({"run_id": keep_run_request.run_id, "job": keep_run_request.job}).encode()

    def deserialize(self, buf: bytes) -> KeepRunRequest:
        snapshot = json.loads(buf)
        return KeepRunRequest(run_id=snapshot["run_id"], job=snapshot["job"])


class KeepRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class KeepRunResponseSnapshot(ts.Serde):

    def serialize(self, keep_run_response: KeepRunResponse) -> bytes:
        return json.dumps({"run_id": keep_run_response.run_id}).encode()

    def deserialize(self, buf: bytes) -> KeepRunResponse:
        snapshot = json.loads(buf)
        return KeepRunResponse(run_id=snapshot["run_id"])


class RunActionsRelay(ts.Relay, typing.Protocol):

    async def run_keep_run(self, keep_run_request: KeepRunRequest) -> KeepRunResponse: ...
