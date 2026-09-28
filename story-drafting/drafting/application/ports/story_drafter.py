from __future__ import annotations

import typing

import tesser.application as ts


class DraftStoriesRequest(ts.Request):

    def __init__(self, job: str) -> None:
        self.job = job


class DraftStoriesResponse(ts.Response):

    def __init__(self, stories: tuple[str, ...]) -> None:
        self.stories = stories


class StoryDrafter(ts.Port, typing.Protocol):

    async def draft_stories(self, draft_stories_request: DraftStoriesRequest) -> DraftStoriesResponse: ...
