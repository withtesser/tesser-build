from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class ProcessJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, description: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.description = description
        self.status = status


class ProcessJtbdRequestSnapshot(ts.Serde):

    def serialize(self, process_jtbd_request: ProcessJtbdRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": process_jtbd_request.jtbd_id,
                "description": process_jtbd_request.description,
                "status": process_jtbd_request.status,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> ProcessJtbdRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("description"), str)
            and isinstance(snapshot.get("status"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a process jtbd request is a jtbd_id, a description, and a status"
            )
        return ProcessJtbdRequest(
            jtbd_id=snapshot["jtbd_id"],
            description=snapshot["description"],
            status=snapshot["status"],
        )


class ProcessJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class ProcessJtbdResponseSnapshot(ts.Serde):

    def serialize(self, process_jtbd_response: ProcessJtbdResponse) -> bytes:
        return json.dumps({"jtbd_id": process_jtbd_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> ProcessJtbdResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a process jtbd response is a jtbd_id")
        return ProcessJtbdResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def run_process_jtbd(self, process_jtbd_request: ProcessJtbdRequest) -> ProcessJtbdResponse: ...
