from __future__ import annotations

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays


@ts.fake
class FakeStoryWriter(ports.StoryWriter):

    def __init__(self) -> None:
        self.jobs: list[str] = []

    async def write_stories(self, write_stories_request: ports.WriteStoriesRequest) -> ports.WriteStoriesResponse:
        self.jobs.append(write_stories_request.job)
        return ports.WriteStoriesResponse(texts=("first", "second"))


class TestWritingActions:

    async def test_writing_asks_the_writer_once_for_the_job_and_answers_what_it_wrote(self) -> None:
        fake_story_writer = FakeStoryWriter()

        write_stories_response = await application.WritingActions(fake_story_writer).write_stories(
            relays.WriteStoriesRequest(job="a job")
        )

        assert fake_story_writer.jobs == ["a job"]
        assert write_stories_response.texts == ("first", "second")
