from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays


class MapToComposeStoriesRequest(ts.Mapper, ports.ComposeStoriesRequest):

    def __init__(self, write_stories_request: relays.WriteStoriesRequest) -> None:
        super().__init__(job=write_stories_request.job)


class MapToWriteStoriesResponse(ts.Mapper, relays.WriteStoriesResponse):

    def __init__(self, compose_stories_response: ports.ComposeStoriesResponse) -> None:
        super().__init__(stories=compose_stories_response.stories)


class DrafterActions(ts.Actions):

    def __init__(self, story_drafter: ports.StoryDrafter) -> None:
        self._story_drafter = story_drafter

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        compose_stories_response = await self._story_drafter.compose_stories(MapToComposeStoriesRequest(write_stories_request))
        return MapToWriteStoriesResponse(compose_stories_response)
