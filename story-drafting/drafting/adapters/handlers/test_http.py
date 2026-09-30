# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import json

import pytest
import tesser.testing as ts

import drafting.adapters.handlers as handlers
import drafting.client as client
import protocol


@ts.fake
class FakeDraftingClient(client.DraftingClient):

    def __init__(self) -> None:
        self.submit_jtbd_requests: list[client.SubmitJtbdRequest] = []
        self.get_jtbd_requests: list[client.GetJtbdRequest] = []

    async def submit_jtbd(self, submit_jtbd_request: client.SubmitJtbdRequest) -> client.SubmitJtbdResponse:
        self.submit_jtbd_requests.append(submit_jtbd_request)
        return client.SubmitJtbdResponse(jtbd_id="jtbd-1", status="drafting_stories")

    async def get_jtbd(self, get_jtbd_request: client.GetJtbdRequest) -> client.GetJtbdResponse:
        self.get_jtbd_requests.append(get_jtbd_request)
        return client.GetJtbdResponse(jtbd_id="jtbd-1", status="drafting_stories", stories=(client.StoryView(given="a job to be done", when="I submit it", then="it is drafting", state="drafted"),))


class TestHttpHandler:

    async def test_submit_jtbd_passes_what_it_reads_and_answers_201_with_the_response_fields(self) -> None:
        fake_drafting_client = FakeDraftingClient()

        http_response = await handlers.HttpHandler(fake_drafting_client).submit_jtbd(
            protocol.HttpRequest(path_params={}, body=b'{"role": "a developer", "i_want": "stories drafted", "so_that": "I can decide"}')
        )

        assert (http_response.status_code, json.loads(http_response.body)) == (201, {"jtbd_id": "jtbd-1", "status": "drafting_stories"})
        assert fake_drafting_client.submit_jtbd_requests == [client.SubmitJtbdRequest(role="a developer", i_want="stories drafted", so_that="I can decide")]

    async def test_submit_jtbd_missing_what_it_reads_is_a_bad_request_that_calls_nothing(self) -> None:
        fake_drafting_client = FakeDraftingClient()

        with pytest.raises(protocol.BadRequest):
            await handlers.HttpHandler(fake_drafting_client).submit_jtbd(protocol.HttpRequest(path_params={}, body=b"{}"))

        assert fake_drafting_client.submit_jtbd_requests == []

    async def test_get_jtbd_passes_what_it_reads_and_answers_200_with_the_response_fields(self) -> None:
        fake_drafting_client = FakeDraftingClient()

        http_response = await handlers.HttpHandler(fake_drafting_client).get_jtbd(
            protocol.HttpRequest(path_params={"jtbd_id": "jtbd-1"}, body=b"")
        )

        assert (http_response.status_code, json.loads(http_response.body)) == (200, {"jtbd_id": "jtbd-1", "status": "drafting_stories", "stories": [{"given": "a job to be done", "when": "I submit it", "then": "it is drafting", "state": "drafted"}]})
        assert fake_drafting_client.get_jtbd_requests == [client.GetJtbdRequest(jtbd_id="jtbd-1")]

    async def test_get_jtbd_missing_what_it_reads_is_a_bad_request_that_calls_nothing(self) -> None:
        fake_drafting_client = FakeDraftingClient()

        with pytest.raises(protocol.BadRequest):
            await handlers.HttpHandler(fake_drafting_client).get_jtbd(protocol.HttpRequest(path_params={}, body=b"{}"))

        assert fake_drafting_client.get_jtbd_requests == []
