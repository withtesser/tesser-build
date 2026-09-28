from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors

PICK_STORIES_PROMISE: typing.Final[str] = "pick_stories"


class AwaitPickStoriesRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class AwaitPickStoriesResponse(ts.Response):

    def __init__(self, stories: tuple[str, ...]) -> None:
        self.stories = stories


class AwaitPickStoriesResponseSnapshot(ts.Serde):

    def serialize(self, await_pick_stories_response: AwaitPickStoriesResponse) -> bytes:
        return json.dumps({"stories": list(await_pick_stories_response.stories)}).encode()

    def deserialize(self, buf: bytes) -> AwaitPickStoriesResponse:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("stories"), list)
            and all(isinstance(story, str) for story in snapshot["stories"])
        ):
            raise errors.invalid("invalid_snapshot", "a pick is the stories picked")
        return AwaitPickStoriesResponse(stories=tuple(snapshot["stories"]))


class RunOrchestratorSignalRelay(ts.Relay, typing.Protocol):

    async def await_pick_stories(
        self, await_pick_stories_request: AwaitPickStoriesRequest
    ) -> AwaitPickStoriesResponse: ...
