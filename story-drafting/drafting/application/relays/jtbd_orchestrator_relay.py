# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class ConductStoryDraftingRequest(ts.Request):

    def __init__(self, jtbd_id: str, role: str, i_want: str, so_that: str) -> None:
        self.jtbd_id = jtbd_id
        self.role = role
        self.i_want = i_want
        self.so_that = so_that


class ConductStoryDraftingRequestSnapshot(ts.Serde):

    def serialize(self, conduct_story_drafting_request: ConductStoryDraftingRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": conduct_story_drafting_request.jtbd_id,
                "role": conduct_story_drafting_request.role,
                "i_want": conduct_story_drafting_request.i_want,
                "so_that": conduct_story_drafting_request.so_that,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> ConductStoryDraftingRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("role"), str)
            and isinstance(snapshot.get("i_want"), str)
            and isinstance(snapshot.get("so_that"), str)
        ):
            raise errors.invalid("invalid_snapshot", "a conduct story drafting request is its jtbd_id, role, i_want, and so_that")
        return ConductStoryDraftingRequest(
            jtbd_id=snapshot["jtbd_id"],
            role=snapshot["role"],
            i_want=snapshot["i_want"],
            so_that=snapshot["so_that"],
        )


class ConductStoryDraftingResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class ConductStoryDraftingResponseSnapshot(ts.Serde):

    def serialize(self, conduct_story_drafting_response: ConductStoryDraftingResponse) -> bytes:
        return json.dumps(
            {
                "jtbd_id": conduct_story_drafting_response.jtbd_id,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> ConductStoryDraftingResponse:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
        ):
            raise errors.invalid("invalid_snapshot", "a conduct story drafting response is its jtbd_id")
        return ConductStoryDraftingResponse(
            jtbd_id=snapshot["jtbd_id"],
        )


class StartConductStoryDraftingResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def start_conduct_story_drafting(self, conduct_story_drafting_request: ConductStoryDraftingRequest) -> StartConductStoryDraftingResponse: ...
