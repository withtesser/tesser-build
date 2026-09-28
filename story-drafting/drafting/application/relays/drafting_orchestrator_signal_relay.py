from __future__ import annotations

import json
import typing

import tesser.application as ts

PICK_STORY_PROMISE: typing.Final[str] = "pick_story"


class AwaitPickStoryRequest(ts.Request):

    def __init__(self, drafting_id: str) -> None:
        self.drafting_id = drafting_id


class AwaitPickStoryResponse(ts.Response):

    def __init__(self, story_id: str) -> None:
        self.story_id = story_id


class AwaitPickStoryResponseSnapshot(ts.Serde):

    def serialize(self, await_pick_story_response: AwaitPickStoryResponse) -> bytes:
        return json.dumps({"story_id": await_pick_story_response.story_id}).encode()

    def deserialize(self, buf: bytes) -> AwaitPickStoryResponse:
        snapshot = json.loads(buf)
        return AwaitPickStoryResponse(story_id=snapshot["story_id"])


class DraftingOrchestratorSignalRelay(ts.Relay, typing.Protocol):

    async def await_pick_story(self, await_pick_story_request: AwaitPickStoryRequest) -> AwaitPickStoryResponse: ...
