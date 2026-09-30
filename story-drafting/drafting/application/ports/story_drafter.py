# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import typing

import tesser.application as ts


class DraftStoriesRequest(ts.Request):

    def __init__(self, role: str) -> None:
        self.role = role


class StoryText(ts.Response):

    def __init__(self, given: str, when: str, then: str) -> None:
        self.given = given
        self.when = when
        self.then = then


class DraftStoriesResponse(ts.Response):

    def __init__(self, story_texts: tuple[StoryText, ...]) -> None:
        self.story_texts = story_texts


class StoryDrafter(ts.Port, typing.Protocol):

    async def draft_stories(self, draft_stories_request: DraftStoriesRequest) -> DraftStoriesResponse: ...
