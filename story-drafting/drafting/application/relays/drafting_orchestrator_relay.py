from __future__ import annotations

import json
import typing

import tesser.application as ts


class ConductDraftingRequest(ts.Request):

    def __init__(self, drafting_id: str, job: str) -> None:
        self.drafting_id = drafting_id
        self.job = job


class ConductDraftingRequestSnapshot(ts.Serde):

    def serialize(self, conduct_drafting_request: ConductDraftingRequest) -> bytes:
        return json.dumps(
            {"drafting_id": conduct_drafting_request.drafting_id, "job": conduct_drafting_request.job}
        ).encode()

    def deserialize(self, buf: bytes) -> ConductDraftingRequest:
        snapshot = json.loads(buf)
        return ConductDraftingRequest(drafting_id=snapshot["drafting_id"], job=snapshot["job"])


class ConductDraftingResponse(ts.Response):

    def __init__(self, drafting_id: str) -> None:
        self.drafting_id = drafting_id


class ConductDraftingResponseSnapshot(ts.Serde):

    def serialize(self, conduct_drafting_response: ConductDraftingResponse) -> bytes:
        return json.dumps({"drafting_id": conduct_drafting_response.drafting_id}).encode()

    def deserialize(self, buf: bytes) -> ConductDraftingResponse:
        snapshot = json.loads(buf)
        return ConductDraftingResponse(drafting_id=snapshot["drafting_id"])


class StartConductDraftingResponse(ts.Response):

    def __init__(self, drafting_id: str) -> None:
        self.drafting_id = drafting_id


class DraftingOrchestratorRelay(ts.Relay, typing.Protocol):

    async def start_conduct_drafting(
        self, conduct_drafting_request: ConductDraftingRequest
    ) -> StartConductDraftingResponse: ...
