from __future__ import annotations

import typing

import tesser.adapters as ts

import calls.client as client
import protocol

_GET_CALL_USAGE: typing.Final[str] = "usage: get-call <call_id>"


class CliHandler(ts.Handler):

    def __init__(self, calls_client: client.CallsClient) -> None:
        self._calls_client = calls_client

    async def place_call(self, cli_request: protocol.CliRequest) -> protocol.CliResponse:
        place_call_response = await self._calls_client.place_call(client.PlaceCallRequest())
        return protocol.CliResponse(exit_code=0, line=protocol.Line(text=place_call_response.call_id))

    async def get_call(self, cli_request: protocol.CliRequest) -> protocol.CliResponse:
        call_id = cli_request.arg(0, "call_id", _GET_CALL_USAGE)
        try:
            get_call_response = await self._calls_client.get_call(client.GetCallRequest(call_id=call_id))
        except client.ERRORS as error:
            match error:
                case client.CallNotFound():
                    return protocol.CliResponse(exit_code=1, line=protocol.Line(text=error.message))
                case _ as never:
                    typing.assert_never(never)
        return protocol.CliResponse(exit_code=0, line=protocol.Line(text=get_call_response.call.person_name))
