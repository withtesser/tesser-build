from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class BeginDraftingRequest(ts.Request):

    def __init__(self, jtbd_id: str, situation: str, motivation: str, outcome: str) -> None:
        self.jtbd_id = jtbd_id
        self.situation = situation
        self.motivation = motivation
        self.outcome = outcome


class BeginDraftingRequestSnapshot(ts.Serde):

    def serialize(self, begin_drafting_request: BeginDraftingRequest) -> bytes:
        return json.dumps(
            {
                "jtbd_id": begin_drafting_request.jtbd_id,
                "situation": begin_drafting_request.situation,
                "motivation": begin_drafting_request.motivation,
                "outcome": begin_drafting_request.outcome,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> BeginDraftingRequest:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
            and isinstance(snapshot.get("situation"), str)
            and isinstance(snapshot.get("motivation"), str)
            and isinstance(snapshot.get("outcome"), str)
        ):
            raise errors.invalid(
                "invalid_snapshot", "a begin drafting request is a jtbd_id, a situation, a motivation, and a outcome"
            )
        return BeginDraftingRequest(
            jtbd_id=snapshot["jtbd_id"],
            situation=snapshot["situation"],
            motivation=snapshot["motivation"],
            outcome=snapshot["outcome"],
        )


class BeginDraftingResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class BeginDraftingResponseSnapshot(ts.Serde):

    def serialize(self, begin_drafting_response: BeginDraftingResponse) -> bytes:
        return json.dumps({"jtbd_id": begin_drafting_response.jtbd_id}).encode()

    def deserialize(self, buf: bytes) -> BeginDraftingResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("jtbd_id"), str)):
            raise errors.invalid("invalid_snapshot", "a begin drafting response is a jtbd_id")
        return BeginDraftingResponse(jtbd_id=snapshot["jtbd_id"])


class StartBeginDraftingResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class JtbdOrchestratorRelay(ts.Relay, typing.Protocol):

    async def start_begin_drafting(self, begin_drafting_request: BeginDraftingRequest) -> StartBeginDraftingResponse: ...
