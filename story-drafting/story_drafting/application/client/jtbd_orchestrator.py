from __future__ import annotations

import typing

import tesser.application as ts

import story_drafting.application.relays as relays


class JtbdOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def conduct_drafting(self, conduct_drafting_request: relays.ConductDraftingRequest) -> relays.ConductDraftingResponse: ...

