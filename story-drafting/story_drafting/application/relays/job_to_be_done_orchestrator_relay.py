from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class WorkThroughJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, statement: str, step: str, draft_count: int, picked_draft: str) -> None:
        self.jtbd_id = jtbd_id
        self.statement = statement
        self.step = step
        self.draft_count = draft_count
        self.picked_draft = picked_draft


class WorkThroughJtbdRequestSnapshot(ts.Serde):

    def serialize(self, work_through_jtbd_request: WorkThroughJtbdRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": work_through_jtbd_request.jtbd_id,
                "statement": work_through_jtbd_request.statement,
                "step": work_through_jtbd_request.step,
                "draft_count": work_through_jtbd_request.draft_count,
                "picked_draft": work_through_jtbd_request.picked_draft,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> WorkThroughJtbdRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("statement"), str)
            and isinstance(snapshot.get("step"), str)
            and isinstance(snapshot.get("draft_count"), int)
            and isinstance(snapshot.get("picked_draft"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a work through jtbd request is a jtbd_id, a statement, a step, a draft_count, and a picked_draft"
            )
        return WorkThroughJtbdRequest(
            jtbd_id=snapshot["jtbd_id"],
            statement=snapshot["statement"],
            step=snapshot["step"],
            draft_count=snapshot["draft_count"],
            picked_draft=snapshot["picked_draft"],
        )


class WorkThroughJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class WorkThroughJtbdResponseSnapshot(ts.Serde):

    def serialize(self, work_through_jtbd_response: WorkThroughJtbdResponse) -> bytes:
        return json.dumps({"jtbd_id": work_through_jtbd_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> WorkThroughJtbdResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a work through jtbd response is a jtbd_id")
        return WorkThroughJtbdResponse(jtbd_id=snapshot["jtbd_id"])


class JobToBeDoneOrchestratorRelay(ts.Relay, typing.Protocol):

    async def run_work_through_jtbd(self, work_through_jtbd_request: WorkThroughJtbdRequest) -> WorkThroughJtbdResponse: ...
