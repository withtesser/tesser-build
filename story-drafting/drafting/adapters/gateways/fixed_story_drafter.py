# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import tesser.adapters as ts

import drafting.application.ports as ports


class FixedStoryDrafter(ts.Gateway):

    async def draft_stories(self, draft_stories_request: ports.DraftStoriesRequest) -> ports.DraftStoriesResponse:
        return ports.DraftStoriesResponse(
            story_texts=(
                ports.StoryText(
                    given=f"{draft_stories_request.role} who wants {draft_stories_request.i_want}",
                    when="they do what the job to be done asks for",
                    then=f"they find that {draft_stories_request.so_that}",
                ),
            )
        )
