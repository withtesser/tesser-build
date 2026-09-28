from __future__ import annotations

import tesser.adapters as ts

import drafting.application.ports as ports


class DeterministicStoryDrafter(ts.Gateway):

    async def draft_stories(self, draft_stories_request: ports.DraftStoriesRequest) -> ports.DraftStoriesResponse:
        return ports.DraftStoriesResponse(
            stories=(
                f"As a developer, I want the first step of this job done so I can sign off on it: "
                f"{draft_stories_request.job}",
                f"As a developer, I want the step after my sign-off built from what I decided: "
                f"{draft_stories_request.job}",
            )
        )
