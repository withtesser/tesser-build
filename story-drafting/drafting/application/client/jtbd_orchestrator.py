# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class JtbdOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def conduct_story_drafting(self, conduct_story_drafting_request: relays.ConductStoryDraftingRequest) -> relays.ConductStoryDraftingResponse: ...
