from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.domain as domain


class MapToWriteStoriesRequest(ts.Mapper, ports.WriteStoriesRequest):

    def __init__(self, job: domain.Job) -> None:
        super().__init__(job=str(job))


class MapToWriteStoriesResponse(ts.Mapper, relays.WriteStoriesResponse):

    def __init__(self, write_stories_response: ports.WriteStoriesResponse) -> None:
        super().__init__(texts=write_stories_response.texts)


class WritingActions(ts.Actions):

    def __init__(self, story_writer: ports.StoryWriter) -> None:
        self._story_writer = story_writer

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        job = domain.Job(write_stories_request.job)
        write_stories_response = await self._story_writer.write_stories(MapToWriteStoriesRequest(job))
        return MapToWriteStoriesResponse(write_stories_response)
