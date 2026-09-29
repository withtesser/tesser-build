from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class MarkJtbdDraftingRequest(ts.Request):

    def __init__(self, jtbd_id: str, description: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.description = description
        self.status = status


class MarkJtbdDraftingRequestSnapshot(ts.Serde):

    def serialize(self, mark_jtbd_drafting_request: MarkJtbdDraftingRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": mark_jtbd_drafting_request.jtbd_id,
                "description": mark_jtbd_drafting_request.description,
                "status": mark_jtbd_drafting_request.status,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> MarkJtbdDraftingRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("description"), str)
            and isinstance(snapshot.get("status"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a mark jtbd drafting request is a jtbd_id, a description, and a status"
            )
        return MarkJtbdDraftingRequest(
            jtbd_id=snapshot["jtbd_id"],
            description=snapshot["description"],
            status=snapshot["status"],
        )


class MarkJtbdDraftingResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class MarkJtbdDraftingResponseSnapshot(ts.Serde):

    def serialize(self, mark_jtbd_drafting_response: MarkJtbdDraftingResponse) -> bytes:
        return json.dumps({"jtbd_id": mark_jtbd_drafting_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> MarkJtbdDraftingResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a mark jtbd drafting response is a jtbd_id")
        return MarkJtbdDraftingResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdActionsRelay(ts.Relay, typing.Protocol):

    async def run_mark_jtbd_drafting(self, mark_jtbd_drafting_request: MarkJtbdDraftingRequest) -> MarkJtbdDraftingResponse: ...
