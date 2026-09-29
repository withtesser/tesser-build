from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors

PICK_STORY_PROMISE: typing.Final[str] = "pick_story"


class AwaitPickStoryRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class AwaitPickStoryResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class AwaitPickStoryResponseSnapshot(ts.Serde):

    def serialize(self, await_pick_story_response: AwaitPickStoryResponse) -> bytes:
        return json.dumps({"run_id": await_pick_story_response.run_id}).encode()

    def deserialize(self, buf: bytes) -> AwaitPickStoryResponse:
        snapshot = json.loads(buf)
        if not (isinstance(snapshot, dict) and isinstance(snapshot.get("run_id"), str)):
            raise errors.invalid("invalid_snapshot", "an await pick story response is a run_id")
        return AwaitPickStoryResponse(run_id=snapshot["run_id"])


class RunOrchestratorSignalRelay(ts.Relay, typing.Protocol):

    async def await_pick_story(self, await_pick_story_request: AwaitPickStoryRequest) -> AwaitPickStoryResponse: ...
