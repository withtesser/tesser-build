from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class DraftForJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, description: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.description = description
        self.status = status


class DraftForJtbdRequestSnapshot(ts.Serde):

    def serialize(self, draft_for_jtbd_request: DraftForJtbdRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": draft_for_jtbd_request.jtbd_id,
                "description": draft_for_jtbd_request.description,
                "status": draft_for_jtbd_request.status,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftForJtbdRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("description"), str)
            and isinstance(snapshot.get("status"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a draft for jtbd request is a jtbd_id, a description, and a status"
            )
        return DraftForJtbdRequest(
            jtbd_id=snapshot["jtbd_id"],
            description=snapshot["description"],
            status=snapshot["status"],
        )


class DraftForJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class DraftForJtbdResponseSnapshot(ts.Serde):

    def serialize(self, draft_for_jtbd_response: DraftForJtbdResponse) -> bytes:
        return json.dumps({"jtbd_id": draft_for_jtbd_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> DraftForJtbdResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a draft for jtbd response is a jtbd_id")
        return DraftForJtbdResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def run_draft_for_jtbd(self, draft_for_jtbd_request: DraftForJtbdRequest) -> DraftForJtbdResponse: ...
