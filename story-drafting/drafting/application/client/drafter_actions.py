# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class DrafterApplicationClient(ts.Client, typing.Protocol):

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse: ...
