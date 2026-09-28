from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.application.client as client
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


class RestateRecordRunRequestSerde(ts.Serde, restate_serde.Serde[relays.RecordRunRequest]):

    def serialize(self, record_run_request: relays.RecordRunRequest | None) -> bytes:
        if record_run_request is None:
            return b""
        return relays.RecordRunRequestSnapshot().serialize(record_run_request)

    def deserialize(self, buf: bytes) -> relays.RecordRunRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.RecordRunRequestSnapshot().deserialize(buf)


class RestateRecordRunResponseSerde(ts.Serde, restate_serde.Serde[relays.RecordRunResponse]):

    def serialize(self, record_run_response: relays.RecordRunResponse | None) -> bytes:
        if record_run_response is None:
            return b""
        return relays.RecordRunResponseSnapshot().serialize(record_run_response)

    def deserialize(self, buf: bytes) -> relays.RecordRunResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.RecordRunResponseSnapshot().deserialize(buf)


class RestateRecordRun(ts.Activity):

    def __init__(self, run_actions_service: restate.Service, run_application_client: client.RunApplicationClient) -> None:
        @run_actions_service.handler(
            input_serde=RestateRecordRunRequestSerde(),
            output_serde=RestateRecordRunResponseSerde(),
        )
        async def record_run(
            restate_context: restate.Context, record_run_request: relays.RecordRunRequest
        ) -> relays.RecordRunResponse:
            return await run_application_client.record_run(record_run_request)

        self.handler = record_run


class RestateWriteStoriesRequestSerde(ts.Serde, restate_serde.Serde[relays.WriteStoriesRequest]):

    def serialize(self, write_stories_request: relays.WriteStoriesRequest | None) -> bytes:
        if write_stories_request is None:
            return b""
        return relays.WriteStoriesRequestSnapshot().serialize(write_stories_request)

    def deserialize(self, buf: bytes) -> relays.WriteStoriesRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.WriteStoriesRequestSnapshot().deserialize(buf)


class RestateWriteStoriesResponseSerde(ts.Serde, restate_serde.Serde[relays.WriteStoriesResponse]):

    def serialize(self, write_stories_response: relays.WriteStoriesResponse | None) -> bytes:
        if write_stories_response is None:
            return b""
        return relays.WriteStoriesResponseSnapshot().serialize(write_stories_response)

    def deserialize(self, buf: bytes) -> relays.WriteStoriesResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.WriteStoriesResponseSnapshot().deserialize(buf)


class RestateWriteStories(ts.Activity):

    def __init__(
        self, story_actions_service: restate.Service, story_application_client: client.StoryApplicationClient
    ) -> None:
        @story_actions_service.handler(
            input_serde=RestateWriteStoriesRequestSerde(),
            output_serde=RestateWriteStoriesResponseSerde(),
        )
        async def write_stories(
            restate_context: restate.Context, write_stories_request: relays.WriteStoriesRequest
        ) -> relays.WriteStoriesResponse:
            return await story_application_client.write_stories(write_stories_request)

        self.handler = write_stories
