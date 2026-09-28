from __future__ import annotations

import typing

import tesser.application as ts


class ComposeStoriesRequest(ts.Request):

    def __init__(self, job: str) -> None:
        self.job = job


class ComposeStoriesResponse(ts.Response):

    def __init__(self, stories: tuple[str, ...]) -> None:
        self.stories = stories


class StoryDrafter(ts.Port, typing.Protocol):

    async def compose_stories(self, compose_stories_request: ComposeStoriesRequest) -> ComposeStoriesResponse: ...
