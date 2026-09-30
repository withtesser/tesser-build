# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestTemplateStoryDrafter:

    async def test_draft_stories_answers_a_draft_stories_response(self) -> None:
        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="stories drafted", so_that="I can accept them"))

        assert isinstance(draft_stories_response, ports.DraftStoriesResponse)

    async def test_draft_stories_drafts_one_story_in_the_words_of_the_job_to_be_done(self) -> None:
        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="stories drafted", so_that="I can accept them"))

        assert [(story_text.given, story_text.when, story_text.then) for story_text in draft_stories_response.story_texts] == [("a developer who wants stories drafted", "a developer asks for stories drafted", "it is done, so that I can accept them")]
