from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import jtbd.application.client as client
import jtbd.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


class RestateMarkJtbdDraftingRequestSerde(ts.Serde, restate_serde.Serde[relays.MarkJtbdDraftingRequest]):

    def serialize(self, mark_jtbd_drafting_request: relays.MarkJtbdDraftingRequest | None) -> bytes:
        if mark_jtbd_drafting_request is None:
            return b""
        return relays.MarkJtbdDraftingRequestSnapshot().serialize(mark_jtbd_drafting_request)

    def deserialize(self, buf: bytes) -> relays.MarkJtbdDraftingRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.MarkJtbdDraftingRequestSnapshot().deserialize(buf)


class RestateMarkJtbdDraftingResponseSerde(ts.Serde, restate_serde.Serde[relays.MarkJtbdDraftingResponse]):

    def serialize(self, mark_jtbd_drafting_response: relays.MarkJtbdDraftingResponse | None) -> bytes:
        if mark_jtbd_drafting_response is None:
            return b""
        return relays.MarkJtbdDraftingResponseSnapshot().serialize(mark_jtbd_drafting_response)

    def deserialize(self, buf: bytes) -> relays.MarkJtbdDraftingResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.MarkJtbdDraftingResponseSnapshot().deserialize(buf)


class RestateMarkJtbdDrafting(ts.Activity):

    def __init__(
        self,
        jtbd_actions_service: restate.Service,
        jtbd_application_client: client.JtbdApplicationClient,
    ) -> None:
        @jtbd_actions_service.handler(
            input_serde=RestateMarkJtbdDraftingRequestSerde(),
            output_serde=RestateMarkJtbdDraftingResponseSerde(),
        )
        async def mark_jtbd_drafting(
            restate_context: restate.Context, mark_jtbd_drafting_request: relays.MarkJtbdDraftingRequest
        ) -> relays.MarkJtbdDraftingResponse:
            return await jtbd_application_client.mark_jtbd_drafting(mark_jtbd_drafting_request)

        self.handler = mark_jtbd_drafting
