from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.application.client as client
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


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


class RestateKeepDraftedStoriesRequestSerde(ts.Serde, restate_serde.Serde[relays.KeepDraftedStoriesRequest]):

    def serialize(self, keep_drafted_stories_request: relays.KeepDraftedStoriesRequest | None) -> bytes:
        if keep_drafted_stories_request is None:
            return b""
        return relays.KeepDraftedStoriesRequestSnapshot().serialize(keep_drafted_stories_request)

    def deserialize(self, buf: bytes) -> relays.KeepDraftedStoriesRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.KeepDraftedStoriesRequestSnapshot().deserialize(buf)


class RestateKeepDraftedStoriesResponseSerde(ts.Serde, restate_serde.Serde[relays.KeepDraftedStoriesResponse]):

    def serialize(self, keep_drafted_stories_response: relays.KeepDraftedStoriesResponse | None) -> bytes:
        if keep_drafted_stories_response is None:
            return b""
        return relays.KeepDraftedStoriesResponseSnapshot().serialize(keep_drafted_stories_response)

    def deserialize(self, buf: bytes) -> relays.KeepDraftedStoriesResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.KeepDraftedStoriesResponseSnapshot().deserialize(buf)


class RestateWriteStories(ts.Activity):

    def __init__(
        self, writing_actions_service: restate.Service, writing_application_client: client.WritingApplicationClient
    ) -> None:
        @writing_actions_service.handler(
            input_serde=RestateWriteStoriesRequestSerde(),
            output_serde=RestateWriteStoriesResponseSerde(),
        )
        async def write_stories(
            restate_context: restate.Context, write_stories_request: relays.WriteStoriesRequest
        ) -> relays.WriteStoriesResponse:
            return await writing_application_client.write_stories(write_stories_request)

        self.handler = write_stories


class RestateKeepDraftedStories(ts.Activity):

    def __init__(
        self, drafting_actions_service: restate.Service, drafting_application_client: client.DraftingApplicationClient
    ) -> None:
        @drafting_actions_service.handler(
            input_serde=RestateKeepDraftedStoriesRequestSerde(),
            output_serde=RestateKeepDraftedStoriesResponseSerde(),
        )
        async def keep_drafted_stories(
            restate_context: restate.Context, keep_drafted_stories_request: relays.KeepDraftedStoriesRequest
        ) -> relays.KeepDraftedStoriesResponse:
            return await drafting_application_client.keep_drafted_stories(keep_drafted_stories_request)

        self.handler = keep_drafted_stories
