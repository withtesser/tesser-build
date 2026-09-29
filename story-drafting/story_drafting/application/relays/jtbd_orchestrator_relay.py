from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class ConductDraftingRequest(ts.Request):

    def __init__(self, jtbd_id: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.status = status


class ConductDraftingRequestSnapshot(ts.Serde):

    def serialize(self, conduct_drafting_request: ConductDraftingRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": conduct_drafting_request.jtbd_id,
                "status": conduct_drafting_request.status,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> ConductDraftingRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("status"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a conduct drafting request is a jtbd_id and a status"
            )
        return ConductDraftingRequest(
            jtbd_id=snapshot["jtbd_id"],
            status=snapshot["status"],
        )


class ConductDraftingResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class ConductDraftingResponseSnapshot(ts.Serde):

    def serialize(self, conduct_drafting_response: ConductDraftingResponse) -> bytes:
        return json.dumps({"jtbd_id": conduct_drafting_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> ConductDraftingResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a conduct drafting response is a jtbd_id")
        return ConductDraftingResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def run_conduct_drafting(self, conduct_drafting_request: ConductDraftingRequest) -> ConductDraftingResponse: ...
