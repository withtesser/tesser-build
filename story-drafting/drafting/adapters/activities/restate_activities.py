from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.application.client as client
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


class RestateWriteDraftsRequestSerde(ts.Serde, restate_serde.Serde[relays.WriteDraftsRequest]):

    def serialize(self, write_drafts_request: relays.WriteDraftsRequest | None) -> bytes:
        if write_drafts_request is None:
            return b""
        return relays.WriteDraftsRequestSnapshot().serialize(write_drafts_request)

    def deserialize(self, buf: bytes) -> relays.WriteDraftsRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.WriteDraftsRequestSnapshot().deserialize(buf)


class RestateWriteDraftsResponseSerde(ts.Serde, restate_serde.Serde[relays.WriteDraftsResponse]):

    def serialize(self, write_drafts_response: relays.WriteDraftsResponse | None) -> bytes:
        if write_drafts_response is None:
            return b""
        return relays.WriteDraftsResponseSnapshot().serialize(write_drafts_response)

    def deserialize(self, buf: bytes) -> relays.WriteDraftsResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.WriteDraftsResponseSnapshot().deserialize(buf)


class RestateWriteDrafts(ts.Activity):

    def __init__(
        self,
        jtbd_actions_service: restate.Service,
        jtbd_application_client: client.JtbdApplicationClient,
    ) -> None:
        @jtbd_actions_service.handler(
            input_serde=RestateWriteDraftsRequestSerde(),
            output_serde=RestateWriteDraftsResponseSerde(),
        )
        async def write_drafts(
            restate_context: restate.Context, write_drafts_request: relays.WriteDraftsRequest
        ) -> relays.WriteDraftsResponse:
            return await jtbd_application_client.write_drafts(write_drafts_request)

        self.handler = write_drafts
