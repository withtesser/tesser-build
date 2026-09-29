from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class RecordSubmissionRequest(ts.Request):

    def __init__(self, jtbd_id: str, situation: str, motivation: str, outcome: str) -> None:
        self.jtbd_id = jtbd_id
        self.situation = situation
        self.motivation = motivation
        self.outcome = outcome


class RecordSubmissionRequestSnapshot(ts.Serde):

    def serialize(self, record_submission_request: RecordSubmissionRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": record_submission_request.jtbd_id,
                "situation": record_submission_request.situation,
                "motivation": record_submission_request.motivation,
                "outcome": record_submission_request.outcome,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> RecordSubmissionRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("situation"), str)
            and isinstance(snapshot.get("motivation"), str)
            and isinstance(snapshot.get("outcome"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a record submission request is a jtbd_id, a situation, a motivation, and a outcome"
            )
        return RecordSubmissionRequest(
            jtbd_id=snapshot["jtbd_id"],
            situation=snapshot["situation"],
            motivation=snapshot["motivation"],
            outcome=snapshot["outcome"],
        )


class RecordSubmissionResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class RecordSubmissionResponseSnapshot(ts.Serde):

    def serialize(self, record_submission_response: RecordSubmissionResponse) -> bytes:
        return json.dumps({"jtbd_id": record_submission_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> RecordSubmissionResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a record submission response is a jtbd_id")
        return RecordSubmissionResponse(jtbd_id=snapshot["jtbd_id"])


class JtbdActionsRelay(ts.Relay, typing.Protocol):

    async def run_record_submission(self, record_submission_request: RecordSubmissionRequest) -> RecordSubmissionResponse: ...
