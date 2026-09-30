# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestFixedStoryDrafter:

    async def test_draft_stories_answers_a_draft_stories_response(self) -> None:
        draft_stories_response = await gateways.FixedStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back"))

        assert isinstance(draft_stories_response, ports.DraftStoriesResponse)

    async def test_draft_stories_drafts_at_least_one_story_text_with_a_given_a_when_and_a_then(self) -> None:
        draft_stories_response = await gateways.FixedStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back"))

        assert len(draft_stories_response.story_texts) >= 1
        assert all(story_text.given != "" and story_text.when != "" and story_text.then != "" for story_text in draft_stories_response.story_texts)

    async def test_draft_stories_drafts_from_the_job_to_be_done_it_is_given(self) -> None:
        draft_stories_response = await gateways.FixedStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back"))

        assert "my checkpoints fixed in advance" in draft_stories_response.story_texts[0].given
        assert "I can step away and come back" in draft_stories_response.story_texts[0].then
