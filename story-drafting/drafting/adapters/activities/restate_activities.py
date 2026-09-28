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
