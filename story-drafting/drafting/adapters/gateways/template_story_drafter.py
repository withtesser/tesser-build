# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import tesser.adapters as ts

import drafting.application.ports as ports


class TemplateStoryDrafter(ts.Gateway):

    async def draft_stories(self, draft_stories_request: ports.DraftStoriesRequest) -> ports.DraftStoriesResponse:
        return ports.DraftStoriesResponse(
            story_texts=(
                ports.StoryText(
                    given=f"I am {draft_stories_request.role}",
                    when=f"I have {draft_stories_request.i_want}",
                    then=f"{draft_stories_request.so_that}",
                ),
            )
        )
