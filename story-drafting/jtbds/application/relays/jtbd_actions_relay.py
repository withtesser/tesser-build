from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class DraftJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, description: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.description = description
        self.status = status


class DraftJtbdRequestSnapshot(ts.Serde):

    def serialize(self, draft_jtbd_request: DraftJtbdRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": draft_jtbd_request.jtbd_id,
                "description": draft_jtbd_request.description,
                "status": draft_jtbd_request.status,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftJtbdRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("description"), str)
            and isinstance(snapshot.get("status"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a draft jtbd request is a jtbd_id, a description, and a status"
            )
        return DraftJtbdRequest(
            jtbd_id=snapshot["jtbd_id"],
            description=snapshot["description"],
            status=snapshot["status"],
        )


class DraftJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class DraftJtbdResponseSnapshot(ts.Serde):

    def serialize(self, draft_jtbd_response: DraftJtbdResponse) -> bytes:
        return json.dumps({"jtbd_id": draft_jtbd_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> DraftJtbdResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a draft jtbd response is a jtbd_id")
        return DraftJtbdResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdActionsRelay(ts.Relay, typing.Protocol):

    async def run_draft_jtbd(self, draft_jtbd_request: DraftJtbdRequest) -> DraftJtbdResponse: ...
