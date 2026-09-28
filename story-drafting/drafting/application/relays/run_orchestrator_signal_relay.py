from __future__ import annotations

import json
import typing

import tesser.application as ts

PICK_STORIES_PROMISE: typing.Final[str] = "pick_stories"


class AwaitPickStoriesRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class AwaitPickStoriesResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class AwaitPickStoriesResponseSnapshot(ts.Serde):

    def serialize(self, await_pick_stories_response: AwaitPickStoriesResponse) -> bytes:
        return json.dumps({"run_id": await_pick_stories_response.run_id}).encode()

    def deserialize(self, buf: bytes) -> AwaitPickStoriesResponse:
        snapshot = json.loads(buf)
        return AwaitPickStoriesResponse(run_id=snapshot["run_id"])


class RunOrchestratorSignalRelay(ts.Relay, typing.Protocol):

    async def await_pick_stories(
        self, await_pick_stories_request: AwaitPickStoriesRequest
    ) -> AwaitPickStoriesResponse: ...
