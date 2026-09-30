# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import json
import typing

import tesser.application as ts

import tesser.errors as errors

ACCEPT_STORIES_PROMISE: typing.Final[str] = "accept_stories"


class AwaitAcceptStoriesRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class AwaitAcceptStoriesResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class AwaitAcceptStoriesResponseSnapshot(ts.Serde):

    def serialize(self, await_accept_stories_response: AwaitAcceptStoriesResponse) -> bytes:
        return json.dumps(
            {
                "jtbd_id": await_accept_stories_response.jtbd_id,
            }
        ).encode()

    def deserialize(self, buf: bytes) -> AwaitAcceptStoriesResponse:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("jtbd_id"), str)
        ):
            raise errors.invalid("invalid_snapshot", "an await accept stories response is its jtbd_id")
        return AwaitAcceptStoriesResponse(
            jtbd_id=snapshot["jtbd_id"],
        )


class JtbdOrchestratorSignalRelay(ts.Relay, typing.Protocol):

    async def await_accept_stories(self, await_accept_stories_request: AwaitAcceptStoriesRequest) -> AwaitAcceptStoriesResponse: ...
