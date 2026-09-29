from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class BeginDraftProcessRequest(ts.Request):

    def __init__(self, jtbd_id: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.status = status


class BeginDraftProcessRequestSnapshot(ts.Serde):

    def serialize(self, begin_draft_process_request: BeginDraftProcessRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": begin_draft_process_request.jtbd_id,
                "status": begin_draft_process_request.status,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> BeginDraftProcessRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("status"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a begin draft process request is a jtbd_id and a status"
            )
        return BeginDraftProcessRequest(
            jtbd_id=snapshot["jtbd_id"],
            status=snapshot["status"],
        )


class BeginDraftProcessResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class BeginDraftProcessResponseSnapshot(ts.Serde):

    def serialize(self, begin_draft_process_response: BeginDraftProcessResponse) -> bytes:
        return json.dumps({"jtbd_id": begin_draft_process_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> BeginDraftProcessResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a begin draft process response is a jtbd_id")
        return BeginDraftProcessResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def run_begin_draft_process(self, begin_draft_process_request: BeginDraftProcessRequest) -> BeginDraftProcessResponse: ...
