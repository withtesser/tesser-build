from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class RecordRunRequest(ts.Request):

    def __init__(
        self,
        run_id: str,
        job: str,
        stage: str,
        stories: tuple[str, ...],
        accepted_stories: tuple[str, ...],
    ) -> None:
        self.run_id = run_id
        self.job = job
        self.stage = stage
        self.stories = stories
        self.accepted_stories = accepted_stories


class RecordRunRequestSnapshot(ts.Serde):

    def serialize(self, record_run_request: RecordRunRequest) -> bytes:
        return json.dumps(
            {
                "run_id": record_run_request.run_id,
                "job": record_run_request.job,
                "stage": record_run_request.stage,
                "stories": list(record_run_request.stories),
                "accepted_stories": list(record_run_request.accepted_stories),
            }
        ).encode()

    def deserialize(self, buf: bytes) -> RecordRunRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("run_id"), str)
            and isinstance(snapshot.get("job"), str)
            and isinstance(snapshot.get("stage"), str)
            and isinstance(snapshot.get("stories"), list)
            and all(isinstance(story, str) for story in snapshot["stories"])
            and isinstance(snapshot.get("accepted_stories"), list)
            and all(isinstance(story, str) for story in snapshot["accepted_stories"])
        ):
            raise errors.invalid(
                "invalid_snapshot",
                "a record run request is a run_id, a job, a stage, its stories, and its accepted stories",
            )
        return RecordRunRequest(
            run_id=snapshot["run_id"],
            job=snapshot["job"],
            stage=snapshot["stage"],
            stories=tuple(snapshot["stories"]),
            accepted_stories=tuple(snapshot["accepted_stories"]),
        )


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
