from __future__ import annotations

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays


@ts.fake
class FakeStoryDrafter(ports.StoryDrafter):

    def __init__(self) -> None:
        self.jobs: list[str] = []

    async def compose_stories(self, compose_stories_request: ports.ComposeStoriesRequest) -> ports.ComposeStoriesResponse:
        self.jobs.append(compose_stories_request.job)
        return ports.ComposeStoriesResponse(stories=("a story", "another story"))


class TestDrafterActions:

    async def test_writing_stories_drafts_them_once_for_the_job_and_answers_what_was_drafted(self) -> None:
        fake_story_drafter = FakeStoryDrafter()
        write_stories_response = await application.DrafterActions(fake_story_drafter).write_stories(
            relays.WriteStoriesRequest(job="a job")
        )
        assert write_stories_response.stories == ("a story", "another story")
        assert fake_story_drafter.jobs == ["a job"]
