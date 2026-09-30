# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestTemplateStoryDrafter:

    async def test_draft_stories_answers_a_draft_stories_response(self) -> None:
        draft_stories_response = await gateways.TemplateStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="stories drafted", so_that="I can accept them"))

        assert isinstance(draft_stories_response, ports.DraftStoriesResponse)
