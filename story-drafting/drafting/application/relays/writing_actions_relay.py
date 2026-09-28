from __future__ import annotations

import json
import typing

import tesser.application as ts


class WriteStoriesRequest(ts.Request):

    def __init__(self, job: str) -> None:
        self.job = job


class WriteStoriesRequestSnapshot(ts.Serde):

    def serialize(self, write_stories_request: WriteStoriesRequest) -> bytes:
        return json.dumps({"job": write_stories_request.job}).encode()

    def deserialize(self, buf: bytes) -> WriteStoriesRequest:
        snapshot = json.loads(buf)
        return WriteStoriesRequest(job=snapshot["job"])


class WriteStoriesResponse(ts.Response):

    def __init__(self, texts: tuple[str, ...]) -> None:
        self.texts = texts


class WriteStoriesResponseSnapshot(ts.Serde):

    def serialize(self, write_stories_response: WriteStoriesResponse) -> bytes:
        return json.dumps({"texts": list(write_stories_response.texts)}).encode()

    def deserialize(self, buf: bytes) -> WriteStoriesResponse:
        snapshot = json.loads(buf)
        return WriteStoriesResponse(texts=tuple(snapshot["texts"]))


class WritingActionsRelay(ts.Relay, typing.Protocol):

    async def run_write_stories(self, write_stories_request: WriteStoriesRequest) -> WriteStoriesResponse: ...
