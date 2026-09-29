from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class InitializeJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.status = status


class InitializeJtbdRequestSnapshot(ts.Serde):

    def serialize(self, initialize_jtbd_request: InitializeJtbdRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": initialize_jtbd_request.jtbd_id,
                "status": initialize_jtbd_request.status,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> InitializeJtbdRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("status"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a initialize jtbd request is a jtbd_id and a status"
            )
        return InitializeJtbdRequest(
            jtbd_id=snapshot["jtbd_id"],
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


class JtbdActionsRelay(ts.Relay, typing.Protocol):

    async def run_initialize_jtbd(self, initialize_jtbd_request: InitializeJtbdRequest) -> InitializeJtbdResponse: ...
