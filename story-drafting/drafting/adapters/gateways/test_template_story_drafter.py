# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestTemplateStoryDrafter:

    async def test_draft_stories_answers_a_draft_stories_response(self) -> None:
        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were"))

        assert isinstance(draft_stories_response, ports.DraftStoriesResponse)

    async def test_draft_stories_drafts_at_least_one_story_text(self) -> None:
        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were"))

        assert len(draft_stories_response.story_texts) >= 1

    async def test_draft_stories_writes_each_story_text_from_the_jtbd(self) -> None:
        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were"))

        assert [(story_text.given, story_text.when, story_text.then) for story_text in draft_stories_response.story_texts] == [("I am a developer", "I have my steps fixed in advance", "I can pick up where we were")]
