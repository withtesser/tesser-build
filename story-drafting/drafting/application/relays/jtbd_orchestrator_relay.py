from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class DraftStoriesRequest(ts.Request):

    def __init__(self, jtbd_id: str, situation: str, motivation: str, outcome: str) -> None:
        self.jtbd_id = jtbd_id
        self.situation = situation
        self.motivation = motivation
        self.outcome = outcome


class DraftStoriesRequestSnapshot(ts.Serde):

    def serialize(self, draft_stories_request: DraftStoriesRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": draft_stories_request.jtbd_id,
                "situation": draft_stories_request.situation,
                "motivation": draft_stories_request.motivation,
                "outcome": draft_stories_request.outcome,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("situation"), str)
            and isinstance(snapshot.get("motivation"), str)
            and isinstance(snapshot.get("outcome"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a draft stories request is a jtbd_id, a situation, a motivation, and a outcome"
            )
        return DraftStoriesRequest(
            jtbd_id=snapshot["jtbd_id"],
            situation=snapshot["situation"],
            motivation=snapshot["motivation"],
            outcome=snapshot["outcome"],
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
