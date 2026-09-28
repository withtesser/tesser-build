from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.application.client as client
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


class RestateKeepRunRequestSerde(ts.Serde, restate_serde.Serde[relays.KeepRunRequest]):

    def serialize(self, keep_run_request: relays.KeepRunRequest | None) -> bytes:
        if keep_run_request is None:
            return b""
        return relays.KeepRunRequestSnapshot().serialize(keep_run_request)

    def deserialize(self, buf: bytes) -> relays.KeepRunRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.KeepRunRequestSnapshot().deserialize(buf)


class RestateKeepRunResponseSerde(ts.Serde, restate_serde.Serde[relays.KeepRunResponse]):

    def serialize(self, keep_run_response: relays.KeepRunResponse | None) -> bytes:
        if keep_run_response is None:
            return b""
        return relays.KeepRunResponseSnapshot().serialize(keep_run_response)

    def deserialize(self, buf: bytes) -> relays.KeepRunResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.KeepRunResponseSnapshot().deserialize(buf)


class RestateKeepRun(ts.Activity):

    def __init__(self, run_actions_service: restate.Service, run_application_client: client.RunApplicationClient) -> None:
        @run_actions_service.handler(
            input_serde=RestateKeepRunRequestSerde(),
            output_serde=RestateKeepRunResponseSerde(),
        )
        async def keep_run(restate_context: restate.Context, keep_run_request: relays.KeepRunRequest) -> relays.KeepRunResponse:
            return await run_application_client.keep_run(keep_run_request)

        self.handler = keep_run


class RestateOfferStoriesRequestSerde(ts.Serde, restate_serde.Serde[relays.OfferStoriesRequest]):

    def serialize(self, offer_stories_request: relays.OfferStoriesRequest | None) -> bytes:
        if offer_stories_request is None:
            return b""
        return relays.OfferStoriesRequestSnapshot().serialize(offer_stories_request)

    def deserialize(self, buf: bytes) -> relays.OfferStoriesRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.OfferStoriesRequestSnapshot().deserialize(buf)


class RestateOfferStoriesResponseSerde(ts.Serde, restate_serde.Serde[relays.OfferStoriesResponse]):

    def serialize(self, offer_stories_response: relays.OfferStoriesResponse | None) -> bytes:
        if offer_stories_response is None:
            return b""
        return relays.OfferStoriesResponseSnapshot().serialize(offer_stories_response)

    def deserialize(self, buf: bytes) -> relays.OfferStoriesResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.OfferStoriesResponseSnapshot().deserialize(buf)


class RestateOfferStories(ts.Activity):

    def __init__(self, run_actions_service: restate.Service, run_application_client: client.RunApplicationClient) -> None:
        @run_actions_service.handler(
            input_serde=RestateOfferStoriesRequestSerde(),
            output_serde=RestateOfferStoriesResponseSerde(),
        )
        async def offer_stories(
            restate_context: restate.Context, offer_stories_request: relays.OfferStoriesRequest
        ) -> relays.OfferStoriesResponse:
            return await run_application_client.offer_stories(offer_stories_request)

        self.handler = offer_stories


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
        self, drafter_actions_service: restate.Service, drafter_application_client: client.DrafterApplicationClient
    ) -> None:
        @drafter_actions_service.handler(
            input_serde=RestateWriteStoriesRequestSerde(),
            output_serde=RestateWriteStoriesResponseSerde(),
        )
        async def write_stories(
            restate_context: restate.Context, write_stories_request: relays.WriteStoriesRequest
        ) -> relays.WriteStoriesResponse:
            return await drafter_application_client.write_stories(write_stories_request)

        self.handler = write_stories
