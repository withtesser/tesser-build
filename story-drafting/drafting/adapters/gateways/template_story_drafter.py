# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import tesser.adapters as ts

import drafting.application.ports as ports


class TemplateStoryDrafter(ts.Gateway):

    async def draft_stories(self, draft_stories_request: ports.DraftStoriesRequest) -> ports.DraftStoriesResponse:
        role = draft_stories_request.role
        i_want = draft_stories_request.i_want
        so_that = draft_stories_request.so_that
        return ports.DraftStoriesResponse(
            story_texts=(
                ports.StoryText(
                    given=f"I am {role}",
                    when=f"I get {i_want}",
                    then=f"{so_that}",
                ),
                ports.StoryText(
                    given=f"I am {role} and I do not yet have {i_want}",
                    when="I try to go on without it",
                    then=f"I am told what is missing before I rely on it, because I need that so that {so_that}",
                ),
            )
        )
