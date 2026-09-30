# pragma: tesser-generated; regenerate from the composition, never edit by hand
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
        self,
        drafter_actions_service: restate.Service,
        drafter_application_client: client.DrafterApplicationClient,
    ) -> None:
        @drafter_actions_service.handler(
            input_serde=RestateDraftStoriesRequestSerde(),
            output_serde=RestateDraftStoriesResponseSerde(),
        )
        async def draft_stories(
            restate_context: restate.Context, draft_stories_request: relays.DraftStoriesRequest
        ) -> relays.DraftStoriesResponse:
            return await drafter_application_client.draft_stories(draft_stories_request)

        self.handler = draft_stories


class RestateRecordStoriesRequestSerde(ts.Serde, restate_serde.Serde[relays.RecordStoriesRequest]):

    def serialize(self, record_stories_request: relays.RecordStoriesRequest | None) -> bytes:
        if record_stories_request is None:
            return b""
        return relays.RecordStoriesRequestSnapshot().serialize(record_stories_request)

    def deserialize(self, buf: bytes) -> relays.RecordStoriesRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.RecordStoriesRequestSnapshot().deserialize(buf)


class RestateRecordStoriesResponseSerde(ts.Serde, restate_serde.Serde[relays.RecordStoriesResponse]):

    def serialize(self, record_stories_response: relays.RecordStoriesResponse | None) -> bytes:
        if record_stories_response is None:
            return b""
        return relays.RecordStoriesResponseSnapshot().serialize(record_stories_response)

    def deserialize(self, buf: bytes) -> relays.RecordStoriesResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.RecordStoriesResponseSnapshot().deserialize(buf)


class RestateRecordStories(ts.Activity):

    def __init__(
        self,
        jtbd_actions_service: restate.Service,
        jtbd_application_client: client.JtbdApplicationClient,
    ) -> None:
        @jtbd_actions_service.handler(
            input_serde=RestateRecordStoriesRequestSerde(),
            output_serde=RestateRecordStoriesResponseSerde(),
        )
        async def record_stories(
            restate_context: restate.Context, record_stories_request: relays.RecordStoriesRequest
        ) -> relays.RecordStoriesResponse:
            return await jtbd_application_client.record_stories(record_stories_request)

        self.handler = record_stories
