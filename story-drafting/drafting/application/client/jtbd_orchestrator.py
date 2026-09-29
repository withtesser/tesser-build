from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class JtbdOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def arrange_drafting(self, arrange_drafting_request: relays.ArrangeDraftingRequest) -> relays.ArrangeDraftingResponse: ...

