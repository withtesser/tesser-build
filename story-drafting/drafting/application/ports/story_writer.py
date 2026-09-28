from __future__ import annotations

import typing

import tesser.application as ts


class WriteStoriesRequest(ts.Request):

    def __init__(self, job: str) -> None:
        self.job = job


class WriteStoriesResponse(ts.Response):

    def __init__(self, texts: tuple[str, ...]) -> None:
        self.texts = texts


class StoryWriter(ts.Port, typing.Protocol):

    async def write_stories(self, write_stories_request: WriteStoriesRequest) -> WriteStoriesResponse: ...
