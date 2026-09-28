from __future__ import annotations

import tesser.application as ts

import drafting.client as client


class DraftingService(ts.ApplicationService):

    async def draft_stories(
        self, draft_stories_request: client.DraftStoriesRequest
    ) -> client.DraftStoriesResponse:
        raise NotImplementedError

    async def get_drafting(self, get_drafting_request: client.GetDraftingRequest) -> client.GetDraftingResponse:
        raise NotImplementedError
