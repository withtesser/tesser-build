from __future__ import annotations

import pytest
import tesser.testing as ts

import calls.adapters.handlers as handlers
import calls.client as client
import protocol


@ts.fake
class FakeCallsClient(client.CallsClient):
    def __init__(self, person_names: dict[str, str]) -> None:
        self.person_names = person_names
        self.placed: list[client.PlaceCallRequest] = []

    async def place_call(self, place_call_request: client.PlaceCallRequest) -> client.PlaceCallResponse:
        self.placed.append(place_call_request)
        return client.PlaceCallResponse(call_id="c7")

    async def get_call(self, get_call_request: client.GetCallRequest) -> client.GetCallResponse:
        if get_call_request.call_id not in self.person_names:
            raise client.CallNotFound(f"no call {get_call_request.call_id!r}")
        return client.GetCallResponse(
            call=client.Call(
                call_id=get_call_request.call_id, person_name=self.person_names[get_call_request.call_id]
            )
        )

    async def person_joined(self, person_joined_request: client.PersonJoinedRequest) -> client.PersonJoinedResponse:
        return client.PersonJoinedResponse(call_id=person_joined_request.call_id)

    async def person_turn_completed(
        self, person_turn_completed_request: client.PersonTurnCompletedRequest
    ) -> client.PersonTurnCompletedResponse:
        return client.PersonTurnCompletedResponse(call_id=person_turn_completed_request.call_id)

    async def attend_call(self, attend_call_request: client.AttendCallRequest) -> client.AttendCallResponse:
        return client.AttendCallResponse(call_id=attend_call_request.call_id)

    async def speak_utterance(
        self, speak_utterance_request: client.SpeakUtteranceRequest
    ) -> client.SpeakUtteranceResponse:
        return client.SpeakUtteranceResponse(call_id=speak_utterance_request.call_id, text=speak_utterance_request.text)


class TestCliHandler:
    async def test_place_call_places_one_call_and_prints_its_call_id(self) -> None:
        fake_calls_client = FakeCallsClient({})
        cli_response = await handlers.CliHandler(fake_calls_client).place_call(protocol.CliRequest(args=()))

        assert len(fake_calls_client.placed) == 1
        assert cli_response == protocol.CliResponse(exit_code=0, line=protocol.Line(text="c7"))

    async def test_get_call_prints_the_name_the_person_said(self) -> None:
        cli_handler = handlers.CliHandler(FakeCallsClient({"c7": "Sarah"}))
        cli_response = await cli_handler.get_call(protocol.CliRequest(args=("c7",)))

        assert cli_response == protocol.CliResponse(exit_code=0, line=protocol.Line(text="Sarah"))

    async def test_a_call_that_was_never_placed_exits_one_with_the_contexts_wording(self) -> None:
        cli_handler = handlers.CliHandler(FakeCallsClient({}))
        cli_response = await cli_handler.get_call(protocol.CliRequest(args=("c8",)))

        assert cli_response == protocol.CliResponse(exit_code=1, line=protocol.Line(text="no call 'c8'"))

    async def test_get_call_without_a_call_id_is_a_usage_error(self) -> None:
        cli_handler = handlers.CliHandler(FakeCallsClient({}))
        with pytest.raises(protocol.UsageError):
            await cli_handler.get_call(protocol.CliRequest(args=()))
