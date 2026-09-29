from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class DraftStoriesRequest(ts.Request):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class DraftStoriesRequestSnapshot(ts.Serde):

    def serialize(self, draft_stories_request: DraftStoriesRequest) -> bytes:
        return json.dumps(
            {
                "run_id": draft_stories_request.run_id,
                "job": draft_stories_request.job,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("run_id"), str)
            and isinstance(snapshot.get("job"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a draft stories request is a run_id and a job"
            )
        return DraftStoriesRequest(
            run_id=snapshot["run_id"],
            job=snapshot["job"],
        )


class DraftStoriesResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class DraftStoriesResponseSnapshot(ts.Serde):

    def serialize(self, draft_stories_response: DraftStoriesResponse) -> bytes:
        return json.dumps({"run_id": draft_stories_response.run_id}).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("run_id"), str)):
            raise errors.invalid("invalid_snapshot", "a draft stories response is a run_id")
        return DraftStoriesResponse(run_id=snapshot["run_id"])


class RunOrchestratorRelay(ts.Relay, typing.Protocol):

    async def run_draft_stories(self, draft_stories_request: DraftStoriesRequest) -> DraftStoriesResponse: ...
