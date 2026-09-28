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

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class AwaitPickStoriesResponseSnapshot(ts.Serde):

    def serialize(self, await_pick_stories_response: AwaitPickStoriesResponse) -> bytes:
        return json.dumps({"run_id": await_pick_stories_response.run_id}).encode()

    def deserialize(self, buf: bytes) -> AwaitPickStoriesResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("run_id"), str)):
            raise errors.invalid("invalid_snapshot", "an await pick stories response is a run_id")
        return AwaitPickStoriesResponse(run_id=snapshot["run_id"])


class RunOrchestratorSignalRelay(ts.Relay, typing.Protocol):

    async def await_pick_stories(
        self, await_pick_stories_request: AwaitPickStoriesRequest
    ) -> AwaitPickStoriesResponse: ...
