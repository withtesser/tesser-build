from __future__ import annotations

import tesser.adapters as ts

import drafting.application.ports as ports


class CannedStoryWriter(ts.Gateway):

    async def write_stories(self, write_stories_request: ports.WriteStoriesRequest) -> ports.WriteStoriesResponse:
        return ports.WriteStoriesResponse(
            stories=(
                f"As a developer, I want the first step of this job fixed in advance, so that: {write_stories_request.job}",
                f"As a developer, I want to weigh in at each checkpoint, so that: {write_stories_request.job}",
            )
        )
