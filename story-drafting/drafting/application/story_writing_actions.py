from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays


class MapToWriteStoriesRequest(ts.Mapper, ports.WriteStoriesRequest):

    def __init__(self, write_stories_request: relays.WriteStoriesRequest) -> None:
        super().__init__(job=write_stories_request.job)


class MapToWriteStoriesResponse(ts.Mapper, relays.WriteStoriesResponse):

    def __init__(self, write_stories_response: ports.WriteStoriesResponse) -> None:
        super().__init__(stories=write_stories_response.stories)


class StoryWritingActions(ts.Actions):

    def __init__(self, story_writing: ports.StoryWriting) -> None:
        self._story_writing = story_writing

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        write_stories_response = await self._story_writing.write_stories(
            MapToWriteStoriesRequest(write_stories_request)
        )
        return MapToWriteStoriesResponse(write_stories_response)
