from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class RecordJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, situation: str, motivation: str, outcome: str) -> None:
        self.jtbd_id = jtbd_id
        self.situation = situation
        self.motivation = motivation
        self.outcome = outcome


class RecordJtbdRequestSnapshot(ts.Serde):

    def serialize(self, record_jtbd_request: RecordJtbdRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": record_jtbd_request.jtbd_id,
                "situation": record_jtbd_request.situation,
                "motivation": record_jtbd_request.motivation,
                "outcome": record_jtbd_request.outcome,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> RecordJtbdRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("situation"), str)
            and isinstance(snapshot.get("motivation"), str)
            and isinstance(snapshot.get("outcome"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a record jtbd request is a jtbd_id, a situation, a motivation, and a outcome"
            )
        return RecordJtbdRequest(
            jtbd_id=snapshot["jtbd_id"],
            situation=snapshot["situation"],
            motivation=snapshot["motivation"],
            outcome=snapshot["outcome"],
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
