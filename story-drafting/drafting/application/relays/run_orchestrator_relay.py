from __future__ import annotations

import json
import typing

import tesser.application as ts

import drafting.application.snapshots as snapshots
import drafting.domain as domain
import tesser.errors as errors


class DraftStoriesRequest(ts.Request):

    def __init__(self, run: domain.Run) -> None:
        self.run = run


class DraftStoriesRequestSnapshot(ts.Serde):

    def serialize(self, draft_stories_request: DraftStoriesRequest) -> bytes:
        return snapshots.RunSnapshot().serialize(draft_stories_request.run)

    def deserialize(self, buf: bytes) -> DraftStoriesRequest:
        return DraftStoriesRequest(run=snapshots.RunSnapshot().deserialize(buf))


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


class StartDraftStoriesResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class RunOrchestratorRelay(ts.Relay, typing.Protocol):

    async def start_draft_stories(self, draft_stories_request: DraftStoriesRequest) -> StartDraftStoriesResponse: ...
