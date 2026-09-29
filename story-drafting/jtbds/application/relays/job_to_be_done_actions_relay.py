from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class InitializeJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, description: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.description = description
        self.status = status


class InitializeJtbdRequestSnapshot(ts.Serde):

    def serialize(self, initialize_jtbd_request: InitializeJtbdRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": initialize_jtbd_request.jtbd_id,
                "description": initialize_jtbd_request.description,
                "status": initialize_jtbd_request.status,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> InitializeJtbdRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("description"), str)
            and isinstance(snapshot.get("status"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a initialize jtbd request is a jtbd_id, a description, and a status"
            )
        return InitializeJtbdRequest(
            jtbd_id=snapshot["jtbd_id"],
            description=snapshot["description"],
            status=snapshot["status"],
        )


class InitializeJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class InitializeJtbdResponseSnapshot(ts.Serde):

    def serialize(self, initialize_jtbd_response: InitializeJtbdResponse) -> bytes:
        return json.dumps({"jtbd_id": initialize_jtbd_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> InitializeJtbdResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a initialize jtbd response is a jtbd_id")
        return InitializeJtbdResponse(jtbd_id=snapshot["jtbd_id"])


class JobToBeDoneActionsRelay(ts.Relay, typing.Protocol):

    async def run_initialize_jtbd(self, initialize_jtbd_request: InitializeJtbdRequest) -> InitializeJtbdResponse: ...
