from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class DraftStoriesRequest(ts.Request):

    def __init__(self, jtbd_id: str, job: str) -> None:
        self.jtbd_id = jtbd_id
        self.job = job


class DraftStoriesRequestSnapshot(ts.Serde):

    def serialize(self, draft_stories_request: DraftStoriesRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": draft_stories_request.jtbd_id,
                "job": draft_stories_request.job,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("job"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a draft stories request is a jtbd_id and a job"
            )
        return DraftStoriesRequest(
            jtbd_id=snapshot["jtbd_id"],
            job=snapshot["job"],
        )


class DraftStoriesResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class DraftStoriesResponseSnapshot(ts.Serde):

    def serialize(self, draft_stories_response: DraftStoriesResponse) -> bytes:
        return json.dumps({"jtbd_id": draft_stories_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a draft stories response is a jtbd_id")
        return DraftStoriesResponse(jtbd_id=snapshot["jtbd_id"])


class StartDraftStoriesResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def start_draft_stories(self, draft_stories_request: DraftStoriesRequest) -> StartDraftStoriesResponse: ...
