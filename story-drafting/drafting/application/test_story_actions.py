# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays


@ts.fake
class FakeStoryDrafter(ports.StoryDrafter):

    def __init__(self) -> None:
        self.draft_stories_requests: list[ports.DraftStoriesRequest] = []

    async def draft_stories(self, draft_stories_request: ports.DraftStoriesRequest) -> ports.DraftStoriesResponse:
        self.draft_stories_requests.append(draft_stories_request)
        return ports.DraftStoriesResponse(story_texts=(ports.StoryText(given="a job to be done", when="I read it", then="its stories are given"),))


class TestStoryActions:

    async def test_draft_stories_asks_its_port_and_answers_what_it_said(self) -> None:
        fake_story_drafter = FakeStoryDrafter()

        draft_stories_response = await application.StoryActions(fake_story_drafter).draft_stories(
            relays.DraftStoriesRequest(role="a developer", i_want="the steps fixed in advance", so_that="I can pick up where we left off")
        )

        assert [(received.role, received.i_want, received.so_that,) for received in fake_story_drafter.draft_stories_requests] == [("a developer", "the steps fixed in advance", "I can pick up where we left off",)]
        assert draft_stories_response.story_texts == (relays.StoryText(given="a job to be done", when="I read it", then="its stories are given"),)
