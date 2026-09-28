from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class DraftingOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def conduct_drafting(
        self, conduct_drafting_request: relays.ConductDraftingRequest
    ) -> relays.ConductDraftingResponse: ...
