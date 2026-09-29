from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import story_drafting.application.client as client
import story_drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


class RestateBeginDraftingRequestSerde(ts.Serde, restate_serde.Serde[relays.BeginDraftingRequest]):

    def serialize(self, begin_drafting_request: relays.BeginDraftingRequest | None) -> bytes:
        if begin_drafting_request is None:
            return b""
        return relays.BeginDraftingRequestSnapshot().serialize(begin_drafting_request)

    def deserialize(self, buf: bytes) -> relays.BeginDraftingRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.BeginDraftingRequestSnapshot().deserialize(buf)


class RestateBeginDraftingResponseSerde(ts.Serde, restate_serde.Serde[relays.BeginDraftingResponse]):

    def serialize(self, begin_drafting_response: relays.BeginDraftingResponse | None) -> bytes:
        if begin_drafting_response is None:
            return b""
        return relays.BeginDraftingResponseSnapshot().serialize(begin_drafting_response)

    def deserialize(self, buf: bytes) -> relays.BeginDraftingResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.BeginDraftingResponseSnapshot().deserialize(buf)


class RestateBeginDrafting(ts.Activity):

    def __init__(
        self,
        jtbd_actions_service: restate.Service,
        jtbd_application_client: client.JtbdApplicationClient,
    ) -> None:
        @jtbd_actions_service.handler(
            input_serde=RestateBeginDraftingRequestSerde(),
            output_serde=RestateBeginDraftingResponseSerde(),
        )
        async def begin_drafting(
            restate_context: restate.Context, begin_drafting_request: relays.BeginDraftingRequest
        ) -> relays.BeginDraftingResponse:
            return await jtbd_application_client.begin_drafting(begin_drafting_request)

        self.handler = begin_drafting
