from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class WriteDraftsRequest(ts.Request):

    def __init__(self, jtbd_id: str, job: str) -> None:
        self.jtbd_id = jtbd_id
        self.job = job


class WriteDraftsRequestSnapshot(ts.Serde):

    def serialize(self, write_drafts_request: WriteDraftsRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": write_drafts_request.jtbd_id,
                "job": write_drafts_request.job,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> WriteDraftsRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("job"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a write drafts request is a jtbd_id and a job"
            )
        return WriteDraftsRequest(
            jtbd_id=snapshot["jtbd_id"],
            job=snapshot["job"],
        )


class WriteDraftsResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class WriteDraftsResponseSnapshot(ts.Serde):

    def serialize(self, write_drafts_response: WriteDraftsResponse) -> bytes:
        return json.dumps({"jtbd_id": write_drafts_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> WriteDraftsResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a write drafts response is a jtbd_id")
        return WriteDraftsResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdActionsRelay(ts.Relay, typing.Protocol):

    async def run_write_drafts(self, write_drafts_request: WriteDraftsRequest) -> WriteDraftsResponse: ...
