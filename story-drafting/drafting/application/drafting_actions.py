from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays


class MapToDraftStoriesRequest(ts.Mapper, ports.DraftStoriesRequest):

    def __init__(self, draft_stories_request: relays.DraftStoriesRequest) -> None:
        super().__init__(job=draft_stories_request.job)


class MapToDraftStoriesResponse(ts.Mapper, relays.DraftStoriesResponse):

    def __init__(self, draft_stories_response: ports.DraftStoriesResponse) -> None:
        super().__init__(stories=draft_stories_response.stories)


class DraftingActions(ts.Actions):

    def __init__(self, story_drafter: ports.StoryDrafter) -> None:
        self._story_drafter = story_drafter

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        draft_stories_response = await self._story_drafter.draft_stories(
            MapToDraftStoriesRequest(draft_stories_request)
        )
        return MapToDraftStoriesResponse(draft_stories_response)
