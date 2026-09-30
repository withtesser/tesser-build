# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import tesser.adapters as ts

import drafting.application.ports as ports


class TemplatedStoryDrafter(ts.Gateway):

    async def draft_stories(self, draft_stories_request: ports.DraftStoriesRequest) -> ports.DraftStoriesResponse:
        return ports.DraftStoriesResponse(
            story_texts=(
                ports.StoryText(
                    given=f"a job to be done: as {draft_stories_request.role}, I want {draft_stories_request.i_want}",
                    when="I submit it to the story-drafting skill",
                    then=f"it is drafted into stories, so that {draft_stories_request.so_that}",
                ),
            )
        )
