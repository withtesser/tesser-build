from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays


class MapToPortWriteStoriesRequest(ts.Mapper, ports.WriteStoriesRequest):

    def __init__(self, write_stories_request: relays.WriteStoriesRequest) -> None:
        super().__init__(job=write_stories_request.job)


class MapToRelayWriteStoriesResponse(ts.Mapper, relays.WriteStoriesResponse):

    def __init__(self, write_stories_response: ports.WriteStoriesResponse) -> None:
        super().__init__(stories=write_stories_response.stories)


class StoryActions(ts.Actions):

    def __init__(self, story_writer: ports.StoryWriter) -> None:
        self._story_writer = story_writer

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        write_stories_response = await self._story_writer.write_stories(MapToPortWriteStoriesRequest(write_stories_request))
        return MapToRelayWriteStoriesResponse(write_stories_response)
