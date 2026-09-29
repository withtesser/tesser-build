from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class DraftJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, situation: str, motivation: str, outcome: str) -> None:
        self.jtbd_id = jtbd_id
        self.situation = situation
        self.motivation = motivation
        self.outcome = outcome


class DraftJtbdRequestSnapshot(ts.Serde):

    def serialize(self, draft_jtbd_request: DraftJtbdRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": draft_jtbd_request.jtbd_id,
                "situation": draft_jtbd_request.situation,
                "motivation": draft_jtbd_request.motivation,
                "outcome": draft_jtbd_request.outcome,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> DraftJtbdRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("situation"), str)
            and isinstance(snapshot.get("motivation"), str)
            and isinstance(snapshot.get("outcome"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a draft jtbd request is a jtbd_id, a situation, a motivation, and a outcome"
            )
        return DraftJtbdRequest(
            jtbd_id=snapshot["jtbd_id"],
            situation=snapshot["situation"],
            motivation=snapshot["motivation"],
            outcome=snapshot["outcome"],
        )


class DraftJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class DraftJtbdResponseSnapshot(ts.Serde):

    def serialize(self, draft_jtbd_response: DraftJtbdResponse) -> bytes:
        return json.dumps({"jtbd_id": draft_jtbd_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> DraftJtbdResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a draft jtbd response is a jtbd_id")
        return DraftJtbdResponse(jtbd_id=snapshot["jtbd_id"])


class StartDraftJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def start_draft_jtbd(self, draft_jtbd_request: DraftJtbdRequest) -> StartDraftJtbdResponse: ...
