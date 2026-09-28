from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class DraftingApplicationClient(ts.Client, typing.Protocol):

    async def keep_drafted_stories(
        self, keep_drafted_stories_request: relays.KeepDraftedStoriesRequest
    ) -> relays.KeepDraftedStoriesResponse: ...
