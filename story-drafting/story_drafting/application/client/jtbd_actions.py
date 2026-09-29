from __future__ import annotations

import typing

import tesser.application as ts

import story_drafting.application.relays as relays


class JtbdApplicationClient(ts.Client, typing.Protocol):

    async def begin_drafting(self, begin_drafting_request: relays.BeginDraftingRequest) -> relays.BeginDraftingResponse: ...
