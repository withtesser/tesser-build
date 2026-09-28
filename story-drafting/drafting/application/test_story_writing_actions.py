from __future__ import annotations

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays


@ts.fake
class FakeStoryWriting(ports.StoryWriting):

    def __init__(self) -> None:
        self.written: list[ports.WriteStoriesRequest] = []

    async def write_stories(self, write_stories_request: ports.WriteStoriesRequest) -> ports.WriteStoriesResponse:
        self.written.append(write_stories_request)
        return ports.WriteStoriesResponse(stories=("As a developer, I want " + write_stories_request.job,))


class TestStoryWritingActions:

    async def test_writing_stories_hands_the_port_the_job(self) -> None:
        fake_story_writing = FakeStoryWriting()
        story_writing_actions = application.StoryWritingActions(fake_story_writing)

        await story_writing_actions.write_stories(relays.WriteStoriesRequest(job="plan a migration"))

        assert [written.job for written in fake_story_writing.written] == ["plan a migration"]

    async def test_writing_stories_answers_the_stories_the_port_wrote(self) -> None:
        story_writing_actions = application.StoryWritingActions(FakeStoryWriting())

        write_stories_response = await story_writing_actions.write_stories(
            relays.WriteStoriesRequest(job="plan a migration")
        )

        assert write_stories_response.stories == ("As a developer, I want plan a migration",)
