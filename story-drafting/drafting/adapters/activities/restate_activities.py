from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.application.client as client
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


class RestateDraftJtbdRequestSerde(ts.Serde, restate_serde.Serde[relays.DraftJtbdRequest]):

    def serialize(self, draft_jtbd_request: relays.DraftJtbdRequest | None) -> bytes:
        if draft_jtbd_request is None:
            return b""
        return relays.DraftJtbdRequestSnapshot().serialize(draft_jtbd_request)

    def deserialize(self, buf: bytes) -> relays.DraftJtbdRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftJtbdRequestSnapshot().deserialize(buf)


class RestateDraftJtbdResponseSerde(ts.Serde, restate_serde.Serde[relays.DraftJtbdResponse]):

    def serialize(self, draft_jtbd_response: relays.DraftJtbdResponse | None) -> bytes:
        if draft_jtbd_response is None:
            return b""
        return relays.DraftJtbdResponseSnapshot().serialize(draft_jtbd_response)

    def deserialize(self, buf: bytes) -> relays.DraftJtbdResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftJtbdResponseSnapshot().deserialize(buf)


class RestateDraftJtbd(ts.Activity):

    def __init__(
        self,
        jtbd_actions_service: restate.Service,
        jtbd_application_client: client.JtbdApplicationClient,
    ) -> None:
        @jtbd_actions_service.handler(
            input_serde=RestateDraftJtbdRequestSerde(),
            output_serde=RestateDraftJtbdResponseSerde(),
        )
        async def draft_jtbd(
            restate_context: restate.Context, draft_jtbd_request: relays.DraftJtbdRequest
        ) -> relays.DraftJtbdResponse:
            return await jtbd_application_client.draft_jtbd(draft_jtbd_request)

        self.handler = draft_jtbd
