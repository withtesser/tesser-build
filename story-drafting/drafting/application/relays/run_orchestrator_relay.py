from __future__ import annotations

import json
import typing

import tesser.application as ts

import drafting.domain as domain


class DraftStoriesRequest(ts.Request):

    def __init__(self, run_id: domain.RunId, job: domain.Job) -> None:
        self.run_id = run_id
        self.job = job


class DraftStoriesRequestSnapshot(ts.Serde):

    def serialize(self, draft_stories_request: DraftStoriesRequest) -> bytes:
        return json.dumps(
            {"run_id": str(draft_stories_request.run_id), "job": str(draft_stories_request.job)}
        ).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesRequest:
        snapshot = json.loads(buf)
        return DraftStoriesRequest(run_id=domain.RunId(snapshot["run_id"]), job=domain.Job(snapshot["job"]))


class DraftStoriesResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class DraftStoriesResponseSnapshot(ts.Serde):

    def serialize(self, draft_stories_response: DraftStoriesResponse) -> bytes:
        return json.dumps({"run_id": draft_stories_response.run_id}).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesResponse:
        snapshot = json.loads(buf)
        return DraftStoriesResponse(run_id=snapshot["run_id"])


class StartDraftStoriesResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class RunOrchestratorRelay(ts.Relay, typing.Protocol):

    async def start_draft_stories(
        self, draft_stories_request: DraftStoriesRequest
    ) -> StartDraftStoriesResponse: ...
