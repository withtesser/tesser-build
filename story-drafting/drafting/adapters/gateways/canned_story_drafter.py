from __future__ import annotations

import tesser.adapters as ts

import drafting.application.ports as ports


class MapToComposeStoriesResponse(ts.Mapper, ports.ComposeStoriesResponse):

    def __init__(self, compose_stories_request: ports.ComposeStoriesRequest) -> None:
        super().__init__(
            stories=(
                f"As a developer, I want the steps of this job fixed in advance: {compose_stories_request.job}",
                f"As a developer, I want to weigh in at each checkpoint of this job: {compose_stories_request.job}",
            )
        )


class CannedStoryDrafter(ts.Gateway):

    async def compose_stories(self, compose_stories_request: ports.ComposeStoriesRequest) -> ports.ComposeStoriesResponse:
        return MapToComposeStoriesResponse(compose_stories_request)
