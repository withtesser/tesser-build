from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class RecordJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, job: str, step: str, draft_count: int, picked_draft: str) -> None:
        self.jtbd_id = jtbd_id
        self.job = job
        self.step = step
        self.draft_count = draft_count
        self.picked_draft = picked_draft


class RecordJtbdRequestSnapshot(ts.Serde):

    def serialize(self, record_jtbd_request: RecordJtbdRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": record_jtbd_request.jtbd_id,
                "job": record_jtbd_request.job,
                "step": record_jtbd_request.step,
                "draft_count": record_jtbd_request.draft_count,
                "picked_draft": record_jtbd_request.picked_draft,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> RecordJtbdRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("job"), str)
            and isinstance(snapshot.get("step"), str)
            and isinstance(snapshot.get("draft_count"), int)
            and isinstance(snapshot.get("picked_draft"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a record jtbd request is a jtbd_id, a job, a step, a draft_count, and a picked_draft"
            )
        return RecordJtbdRequest(
            jtbd_id=snapshot["jtbd_id"],
            job=snapshot["job"],
            step=snapshot["step"],
            draft_count=snapshot["draft_count"],
            picked_draft=snapshot["picked_draft"],
        )


class RecordJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class RecordJtbdResponseSnapshot(ts.Serde):

    def serialize(self, record_jtbd_response: RecordJtbdResponse) -> bytes:
        return json.dumps({"jtbd_id": record_jtbd_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> RecordJtbdResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a record jtbd response is a jtbd_id")
        return RecordJtbdResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdActionsRelay(ts.Relay, typing.Protocol):

    async def run_record_jtbd(self, record_jtbd_request: RecordJtbdRequest) -> RecordJtbdResponse: ...
