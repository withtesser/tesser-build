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
        story_actions_service: restate.Service,
        story_application_client: client.StoryApplicationClient,
    ) -> None:
        @story_actions_service.handler(
            input_serde=RestateDraftStoriesRequestSerde(),
            output_serde=RestateDraftStoriesResponseSerde(),
        )
        async def draft_stories(
            restate_context: restate.Context, draft_stories_request: relays.DraftStoriesRequest
        ) -> relays.DraftStoriesResponse:
            return await story_application_client.draft_stories(draft_stories_request)

        self.handler = draft_stories


class RestateRecordDraftedStoriesRequestSerde(ts.Serde, restate_serde.Serde[relays.RecordDraftedStoriesRequest]):

    def serialize(self, record_drafted_stories_request: relays.RecordDraftedStoriesRequest | None) -> bytes:
        if record_drafted_stories_request is None:
            return b""
        return relays.RecordDraftedStoriesRequestSnapshot().serialize(record_drafted_stories_request)

    def deserialize(self, buf: bytes) -> relays.RecordDraftedStoriesRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.RecordDraftedStoriesRequestSnapshot().deserialize(buf)


class RestateRecordDraftedStoriesResponseSerde(ts.Serde, restate_serde.Serde[relays.RecordDraftedStoriesResponse]):

    def serialize(self, record_drafted_stories_response: relays.RecordDraftedStoriesResponse | None) -> bytes:
        if record_drafted_stories_response is None:
            return b""
        return relays.RecordDraftedStoriesResponseSnapshot().serialize(record_drafted_stories_response)

    def deserialize(self, buf: bytes) -> relays.RecordDraftedStoriesResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.RecordDraftedStoriesResponseSnapshot().deserialize(buf)


class RestateRecordDraftedStories(ts.Activity):

    def __init__(
        self,
        jtbd_actions_service: restate.Service,
        jtbd_application_client: client.JtbdApplicationClient,
    ) -> None:
        @jtbd_actions_service.handler(
            input_serde=RestateRecordDraftedStoriesRequestSerde(),
            output_serde=RestateRecordDraftedStoriesResponseSerde(),
        )
        async def record_drafted_stories(
            restate_context: restate.Context, record_drafted_stories_request: relays.RecordDraftedStoriesRequest
        ) -> relays.RecordDraftedStoriesResponse:
            return await jtbd_application_client.record_drafted_stories(record_drafted_stories_request)

        self.handler = record_drafted_stories
