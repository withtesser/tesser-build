# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestTemplateStoryDrafter:

    async def test_draft_stories_answers_a_draft_stories_response(self) -> None:
        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="stories drafted", so_that="I can accept them"))

        assert isinstance(draft_stories_response, ports.DraftStoriesResponse)

    async def test_draft_stories_drafts_at_least_one_story_text(self) -> None:
        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="stories drafted", so_that="I can accept them"))

        assert len(draft_stories_response.story_texts) >= 1

    async def test_draft_stories_writes_the_job_to_be_done_into_its_story_text(self) -> None:
        draft_stories_request = ports.DraftStoriesRequest(role="a developer", i_want="stories drafted", so_that="I can accept them")

        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(draft_stories_request)

        assert [(draft_stories_request.role in story_text.given, draft_stories_request.i_want in story_text.when, draft_stories_request.so_that in story_text.then) for story_text in draft_stories_response.story_texts] == [(True, True, True)]
