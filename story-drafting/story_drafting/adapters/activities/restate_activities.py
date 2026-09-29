from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import story_drafting.application.client as client
import story_drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"


class RestateRecordJtbdRequestSerde(ts.Serde, restate_serde.Serde[relays.RecordJtbdRequest]):

    def serialize(self, record_jtbd_request: relays.RecordJtbdRequest | None) -> bytes:
        if record_jtbd_request is None:
            return b""
        return relays.RecordJtbdRequestSnapshot().serialize(record_jtbd_request)

    def deserialize(self, buf: bytes) -> relays.RecordJtbdRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.RecordJtbdRequestSnapshot().deserialize(buf)


class RestateRecordJtbdResponseSerde(ts.Serde, restate_serde.Serde[relays.RecordJtbdResponse]):

    def serialize(self, record_jtbd_response: relays.RecordJtbdResponse | None) -> bytes:
        if record_jtbd_response is None:
            return b""
        return relays.RecordJtbdResponseSnapshot().serialize(record_jtbd_response)

    def deserialize(self, buf: bytes) -> relays.RecordJtbdResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.RecordJtbdResponseSnapshot().deserialize(buf)


class RestateRecordJtbd(ts.Activity):

    def __init__(
        self,
        jtbd_actions_service: restate.Service,
        jtbd_application_client: client.JtbdApplicationClient,
    ) -> None:
        @jtbd_actions_service.handler(
            input_serde=RestateRecordJtbdRequestSerde(),
            output_serde=RestateRecordJtbdResponseSerde(),
        )
        async def record_jtbd(
            restate_context: restate.Context, record_jtbd_request: relays.RecordJtbdRequest
        ) -> relays.RecordJtbdResponse:
            return await jtbd_application_client.record_jtbd(record_jtbd_request)

        self.handler = record_jtbd
