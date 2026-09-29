from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class ArrangeDraftingRequest(ts.Request):

    def __init__(self, jtbd_id: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.status = status


class ArrangeDraftingRequestSnapshot(ts.Serde):

    def serialize(self, arrange_drafting_request: ArrangeDraftingRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": arrange_drafting_request.jtbd_id,
                "status": arrange_drafting_request.status,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> ArrangeDraftingRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("status"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a arrange drafting request is a jtbd_id and a status"
            )
        return ArrangeDraftingRequest(
            jtbd_id=snapshot["jtbd_id"],
            status=snapshot["status"],
        )


class ArrangeDraftingResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class ArrangeDraftingResponseSnapshot(ts.Serde):

    def serialize(self, arrange_drafting_response: ArrangeDraftingResponse) -> bytes:
        return json.dumps({"jtbd_id": arrange_drafting_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> ArrangeDraftingResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a arrange drafting response is a jtbd_id")
        return ArrangeDraftingResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def run_arrange_drafting(self, arrange_drafting_request: ArrangeDraftingRequest) -> ArrangeDraftingResponse: ...
