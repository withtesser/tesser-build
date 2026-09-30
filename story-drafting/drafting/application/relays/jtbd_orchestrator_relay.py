# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class DraftJtbdStoriesRequest(ts.Request):

    def __init__(self, jtbd_id: str, role: str, i_want: str, so_that: str) -> None:
        self.jtbd_id = jtbd_id
        self.role = role
        self.i_want = i_want
        self.so_that = so_that


class DraftJtbdStoriesRequestSnapshot(ts.Serde):

    def serialize(self, draft_jtbd_stories_request: DraftJtbdStoriesRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": draft_jtbd_stories_request.jtbd_id,
                "role": draft_jtbd_stories_request.role,
                "i_want": draft_jtbd_stories_request.i_want,
                "so_that": draft_jtbd_stories_request.so_that,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftJtbdStoriesRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("role"), str)
            and isinstance(snapshot.get("i_want"), str)
            and isinstance(snapshot.get("so_that"), str)
        ):
            raise errors.invalid("invalid_snapshot", "a draft jtbd stories request is its jtbd_id, role, i_want, and so_that")
        return DraftJtbdStoriesRequest(
            jtbd_id=snapshot["jtbd_id"],
            role=snapshot["role"],
            i_want=snapshot["i_want"],
            so_that=snapshot["so_that"],
        )


class DraftJtbdStoriesResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class DraftJtbdStoriesResponseSnapshot(ts.Serde):

    def serialize(self, draft_jtbd_stories_response: DraftJtbdStoriesResponse) -> bytes:
        return json.dumps(
            {
                "jtbd_id": draft_jtbd_stories_response.jtbd_id,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftJtbdStoriesResponse:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
        ):
            raise errors.invalid("invalid_snapshot", "a draft jtbd stories response is its jtbd_id")
        return DraftJtbdStoriesResponse(
            jtbd_id=snapshot["jtbd_id"],
        )


class StartDraftJtbdStoriesResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def start_draft_jtbd_stories(self, draft_jtbd_stories_request: DraftJtbdStoriesRequest) -> StartDraftJtbdStoriesResponse: ...
