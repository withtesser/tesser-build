from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class JtbdOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse: ...

