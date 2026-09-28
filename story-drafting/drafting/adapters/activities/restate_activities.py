from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.application.client as client
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


class RestateDraftStoriesRequestSerde(ts.Serde, restate_serde.Serde[relays.DraftStoriesRequest]):

    def serialize(self, draft_stories_request: relays.DraftStoriesRequest | None) -> bytes:
        if draft_stories_request is None:
            return b""
        return relays.DraftStoriesRequestSnapshot().serialize(draft_stories_request)

    def deserialize(self, buf: bytes) -> relays.DraftStoriesRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftStoriesRequestSnapshot().deserialize(buf)


class RestateDraftStoriesResponseSerde(ts.Serde, restate_serde.Serde[relays.DraftStoriesResponse]):

    def serialize(self, draft_stories_response: relays.DraftStoriesResponse | None) -> bytes:
        if draft_stories_response is None:
            return b""
        return relays.DraftStoriesResponseSnapshot().serialize(draft_stories_response)

    def deserialize(self, buf: bytes) -> relays.DraftStoriesResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftStoriesResponseSnapshot().deserialize(buf)


class RestateDraftStories(ts.Activity):

    def __init__(
        self, drafting_actions_service: restate.Service, drafting_application_client: client.DraftingApplicationClient
    ) -> None:
        @drafting_actions_service.handler(
            input_serde=RestateDraftStoriesRequestSerde(),
            output_serde=RestateDraftStoriesResponseSerde(),
        )
        async def draft_stories(
            restate_context: restate.Context, draft_stories_request: relays.DraftStoriesRequest
        ) -> relays.DraftStoriesResponse:
            return await drafting_application_client.draft_stories(draft_stories_request)

        self.handler = draft_stories


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

    def __init__(
        self, run_actions_service: restate.Service, run_application_client: client.RunApplicationClient
    ) -> None:
        @run_actions_service.handler(
            input_serde=RestateRecordRunRequestSerde(),
            output_serde=RestateRecordRunResponseSerde(),
        )
        async def record_run(
            restate_context: restate.Context, record_run_request: relays.RecordRunRequest
        ) -> relays.RecordRunResponse:
            return await run_application_client.record_run(record_run_request)

        self.handler = record_run
