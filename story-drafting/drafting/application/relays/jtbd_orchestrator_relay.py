# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class StoryDraftingRequest(ts.Request):

    def __init__(self, jtbd_id: str, role: str, i_want: str, so_that: str) -> None:
        self.jtbd_id = jtbd_id
        self.role = role
        self.i_want = i_want
        self.so_that = so_that


class StoryDraftingRequestSnapshot(ts.Serde):

    def serialize(self, story_drafting_request: StoryDraftingRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": story_drafting_request.jtbd_id,
                "role": story_drafting_request.role,
                "i_want": story_drafting_request.i_want,
                "so_that": story_drafting_request.so_that,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> StoryDraftingRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("role"), str)
            and isinstance(snapshot.get("i_want"), str)
            and isinstance(snapshot.get("so_that"), str)
        ):
            raise errors.invalid("invalid_snapshot", "a story drafting request is its jtbd_id, role, i_want, and so_that")
        return StoryDraftingRequest(
            jtbd_id=snapshot["jtbd_id"],
            role=snapshot["role"],
            i_want=snapshot["i_want"],
            so_that=snapshot["so_that"],
        )


class StoryDraftingResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class StoryDraftingResponseSnapshot(ts.Serde):

    def serialize(self, story_drafting_response: StoryDraftingResponse) -> bytes:
        return json.dumps(
            {
                "jtbd_id": story_drafting_response.jtbd_id,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> StoryDraftingResponse:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
        ):
            raise errors.invalid("invalid_snapshot", "a story drafting response is its jtbd_id")
        return StoryDraftingResponse(
            jtbd_id=snapshot["jtbd_id"],
        )


class StartStoryDraftingResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def start_story_drafting(self, story_drafting_request: StoryDraftingRequest) -> StartStoryDraftingResponse: ...
