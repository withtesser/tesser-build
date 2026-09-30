# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import drafting.adapters.gateways as gateways
import drafting.application.ports as ports


class TestTemplatedStoryDrafter:

    async def test_draft_stories_answers_a_draft_stories_response(self) -> None:
        draft_stories_response = await gateways.TemplatedStoryDrafter().draft_stories(ports.DraftStoriesRequest(role="a developer", i_want="stories drafted for my job to be done", so_that="I can decide which to keep"))

        assert isinstance(draft_stories_response, ports.DraftStoriesResponse)
