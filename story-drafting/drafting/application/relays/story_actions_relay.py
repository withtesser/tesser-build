from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors


class WriteStoriesRequest(ts.Request):

    def __init__(self, job: str) -> None:
        self.job = job


class WriteStoriesRequestSnapshot(ts.Serde):

    def serialize(self, write_stories_request: WriteStoriesRequest) -> bytes:
        return json.dumps({"job": write_stories_request.job}).encode()

    def deserialize(self, buf: bytes) -> WriteStoriesRequest:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("job"), str)):
            raise errors.invalid("invalid_snapshot", "a write stories request is a job")
        return WriteStoriesRequest(job=snapshot["job"])


class WriteStoriesResponse(ts.Response):

    def __init__(self, stories: tuple[str, ...]) -> None:
        self.stories = stories


class WriteStoriesResponseSnapshot(ts.Serde):

    def serialize(self, write_stories_response: WriteStoriesResponse) -> bytes:
        return json.dumps({"stories": list(write_stories_response.stories)}).encode()

    def deserialize(self, buf: bytes) -> WriteStoriesResponse:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("stories"), list)
            and all(isinstance(story, str) for story in snapshot["stories"])
        ):
            raise errors.invalid("invalid_snapshot", "a write stories response is a list of stories")
        return WriteStoriesResponse(stories=tuple(snapshot["stories"]))


class StoryActionsRelay(ts.Relay, typing.Protocol):

    async def run_write_stories(self, write_stories_request: WriteStoriesRequest) -> WriteStoriesResponse: ...
