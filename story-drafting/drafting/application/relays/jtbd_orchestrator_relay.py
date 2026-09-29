from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class WorkThroughJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, situation: str, motivation: str, outcome: str) -> None:
        self.jtbd_id = jtbd_id
        self.situation = situation
        self.motivation = motivation
        self.outcome = outcome


class WorkThroughJtbdRequestSnapshot(ts.Serde):

    def serialize(self, work_through_jtbd_request: WorkThroughJtbdRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": work_through_jtbd_request.jtbd_id,
                "situation": work_through_jtbd_request.situation,
                "motivation": work_through_jtbd_request.motivation,
                "outcome": work_through_jtbd_request.outcome,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> WorkThroughJtbdRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("situation"), str)
            and isinstance(snapshot.get("motivation"), str)
            and isinstance(snapshot.get("outcome"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a work through jtbd request is a jtbd_id, a situation, a motivation, and a outcome"
            )
        return WorkThroughJtbdRequest(
            jtbd_id=snapshot["jtbd_id"],
            situation=snapshot["situation"],
            motivation=snapshot["motivation"],
            outcome=snapshot["outcome"],
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


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def run_work_through_jtbd(self, work_through_jtbd_request: WorkThroughJtbdRequest) -> WorkThroughJtbdResponse: ...
