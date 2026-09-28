from __future__ import annotations

import tesser.adapters as ts

import drafting.application.ports as ports


class FixedStoryWriting(ts.Gateway):

    async def write_stories(self, write_stories_request: ports.WriteStoriesRequest) -> ports.WriteStoriesResponse:
        return ports.WriteStoriesResponse(
            stories=(
                f"As a developer, I want the steps of this job fixed in advance: {write_stories_request.job}",
                f"As a developer, I want a checkpoint where I weigh in before this job goes on: {write_stories_request.job}",
            )
        )
