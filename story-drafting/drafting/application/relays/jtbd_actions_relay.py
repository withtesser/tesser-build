# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class DraftStoriesRequest(ts.Request):

    def __init__(self, jtbd_id: str, role: str, i_want: str, so_that: str) -> None:
        self.jtbd_id = jtbd_id
        self.role = role
        self.i_want = i_want
        self.so_that = so_that


class DraftStoriesRequestSnapshot(ts.Serde):

    def serialize(self, draft_stories_request: DraftStoriesRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": draft_stories_request.jtbd_id,
                "role": draft_stories_request.role,
                "i_want": draft_stories_request.i_want,
                "so_that": draft_stories_request.so_that,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("role"), str)
            and isinstance(snapshot.get("i_want"), str)
            and isinstance(snapshot.get("so_that"), str)
        ):
            raise errors.invalid("invalid_snapshot", "a draft stories request is its jtbd_id, role, i_want, and so_that")
        return DraftStoriesRequest(
            jtbd_id=snapshot["jtbd_id"],
            role=snapshot["role"],
            i_want=snapshot["i_want"],
            so_that=snapshot["so_that"],
        )


class DraftStoriesResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class DraftStoriesResponseSnapshot(ts.Serde):

    def serialize(self, draft_stories_response: DraftStoriesResponse) -> bytes:
        return json.dumps(
            {
                "jtbd_id": draft_stories_response.jtbd_id,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftStoriesResponse:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
        ):
            raise errors.invalid("invalid_snapshot", "a draft stories response is its jtbd_id")
        return DraftStoriesResponse(
            jtbd_id=snapshot["jtbd_id"],
        )


class JtbdActionsRelay(ts.Relay, typing.Protocol):

    async def run_draft_stories(self, draft_stories_request: DraftStoriesRequest) -> DraftStoriesResponse: ...
