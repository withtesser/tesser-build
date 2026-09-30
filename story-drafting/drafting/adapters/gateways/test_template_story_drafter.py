# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestTemplateStoryDrafter:

    async def test_draft_stories_answers_a_draft_stories_response(self) -> None:
        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it"))

        assert isinstance(draft_stories_response, ports.DraftStoriesResponse)

    async def test_draft_stories_yields_at_least_one_story_text(self) -> None:
        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it"))

        assert len(draft_stories_response.story_texts) >= 1

    async def test_draft_stories_fills_its_templates_with_the_job_to_be_done_parts(self) -> None:
        draft_stories_request = ports.DraftStoriesRequest(role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it")

        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(draft_stories_request)

        assert [(story_text.given, story_text.when, story_text.then) for story_text in draft_stories_response.story_texts] == [("a traveller", "I want one itinerary we all agreed on", "I get it, so that I can book it")]
