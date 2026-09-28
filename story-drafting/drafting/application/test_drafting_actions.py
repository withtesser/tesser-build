from __future__ import annotations

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays


@ts.fake
class FakeStoryDrafter(ports.StoryDrafter):

    def __init__(self, stories: tuple[str, ...]) -> None:
        self._stories = stories
        self.asked: list[ports.DraftStoriesRequest] = []

    async def draft_stories(self, draft_stories_request: ports.DraftStoriesRequest) -> ports.DraftStoriesResponse:
        self.asked.append(draft_stories_request)
        return ports.DraftStoriesResponse(stories=self._stories)


class TestDraftingActions:

    async def test_drafting_asks_the_drafter_about_the_job(self) -> None:
        fake_story_drafter = FakeStoryDrafter(("a story",))

        await application.DraftingActions(fake_story_drafter).draft_stories(
            relays.DraftStoriesRequest(run_id="r1", job="ship a release")
        )

        assert [draft_stories_request.job for draft_stories_request in fake_story_drafter.asked] == ["ship a release"]

    async def test_drafting_answers_the_stories_the_drafter_wrote(self) -> None:
        draft_stories_response = await application.DraftingActions(FakeStoryDrafter(("first", "second"))).draft_stories(
            relays.DraftStoriesRequest(run_id="r1", job="ship a release")
        )

        assert draft_stories_response.stories == ("first", "second")
