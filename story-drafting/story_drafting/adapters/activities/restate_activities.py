from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import story_drafting.application.client as client
import story_drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


class RestateInitializeJtbdRequestSerde(ts.Serde, restate_serde.Serde[relays.InitializeJtbdRequest]):

    def serialize(self, initialize_jtbd_request: relays.InitializeJtbdRequest | None) -> bytes:
        if initialize_jtbd_request is None:
            return b""
        return relays.InitializeJtbdRequestSnapshot().serialize(initialize_jtbd_request)

    def deserialize(self, buf: bytes) -> relays.InitializeJtbdRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.InitializeJtbdRequestSnapshot().deserialize(buf)


class RestateInitializeJtbdResponseSerde(ts.Serde, restate_serde.Serde[relays.InitializeJtbdResponse]):

    def serialize(self, initialize_jtbd_response: relays.InitializeJtbdResponse | None) -> bytes:
        if initialize_jtbd_response is None:
            return b""
        return relays.InitializeJtbdResponseSnapshot().serialize(initialize_jtbd_response)

    def deserialize(self, buf: bytes) -> relays.InitializeJtbdResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.InitializeJtbdResponseSnapshot().deserialize(buf)


class RestateInitializeJtbd(ts.Activity):

    def __init__(
        self,
        jtbd_actions_service: restate.Service,
        jtbd_application_client: client.JtbdApplicationClient,
    ) -> None:
        @jtbd_actions_service.handler(
            input_serde=RestateInitializeJtbdRequestSerde(),
            output_serde=RestateInitializeJtbdResponseSerde(),
        )
        async def initialize_jtbd(
            restate_context: restate.Context, initialize_jtbd_request: relays.InitializeJtbdRequest
        ) -> relays.InitializeJtbdResponse:
            return await jtbd_application_client.initialize_jtbd(initialize_jtbd_request)

        self.handler = initialize_jtbd
