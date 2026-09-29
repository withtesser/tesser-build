from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class BeginDraftingRequest(ts.Request):

    def __init__(self, jtbd_id: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.status = status


class BeginDraftingRequestSnapshot(ts.Serde):

    def serialize(self, begin_drafting_request: BeginDraftingRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": begin_drafting_request.jtbd_id,
                "status": begin_drafting_request.status,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> BeginDraftingRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("status"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a begin drafting request is a jtbd_id and a status"
            )
        return BeginDraftingRequest(
            jtbd_id=snapshot["jtbd_id"],
            status=snapshot["status"],
        )


class BeginDraftingResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class BeginDraftingResponseSnapshot(ts.Serde):

    def serialize(self, begin_drafting_response: BeginDraftingResponse) -> bytes:
        return json.dumps({"jtbd_id": begin_drafting_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> BeginDraftingResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a begin drafting response is a jtbd_id")
        return BeginDraftingResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdActionsRelay(ts.Relay, typing.Protocol):

    async def run_begin_drafting(self, begin_drafting_request: BeginDraftingRequest) -> BeginDraftingResponse: ...
