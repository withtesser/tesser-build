from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class ConductRunRequest(ts.Request):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class ConductRunRequestSnapshot(ts.Serde):

    def serialize(self, conduct_run_request: ConductRunRequest) -> bytes:
        return json.dumps(
            {
                "run_id": conduct_run_request.run_id,
                "job": conduct_run_request.job,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> ConductRunRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("run_id"), str)
            and isinstance(snapshot.get("job"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a conduct run request is a run_id and a job"
            )
        return ConductRunRequest(
            run_id=snapshot["run_id"],
            job=snapshot["job"],
        )


class ConductRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class ConductRunResponseSnapshot(ts.Serde):

    def serialize(self, conduct_run_response: ConductRunResponse) -> bytes:
        return json.dumps({"run_id": conduct_run_response.run_id}).encode()

    def deserialize(self, buf: bytes) -> ConductRunResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("run_id"), str)):
            raise errors.invalid("invalid_snapshot", "a conduct run response is a run_id")
        return ConductRunResponse(run_id=snapshot["run_id"])


class RunOrchestratorRelay(ts.Relay, typing.Protocol):

    async def run_conduct_run(self, conduct_run_request: ConductRunRequest) -> ConductRunResponse: ...
