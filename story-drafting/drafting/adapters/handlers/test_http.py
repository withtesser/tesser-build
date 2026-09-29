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
        self.open_run_requests: list[client.OpenRunRequest] = []
        self.get_run_requests: list[client.GetRunRequest] = []

    async def open_run(self, open_run_request: client.OpenRunRequest) -> client.OpenRunResponse:
        self.open_run_requests.append(open_run_request)
        return client.OpenRunResponse(run_id="run-1")

    async def get_run(self, get_run_request: client.GetRunRequest) -> client.GetRunResponse:
        self.get_run_requests.append(get_run_request)
        return client.GetRunResponse(client.Run(run_id="run-1", job="Plan a trip"))


class TestHttpHandler:

    async def test_open_run_passes_each_body_field_as_its_field_and_answers_the_run_id(self) -> None:
        fake_drafting_client = FakeDraftingClient()

        http_response = await handlers.HttpHandler(fake_drafting_client).open_run(
            protocol.HttpRequest(
                path_params={}, body=json.dumps({"job": "Plan a trip"}).encode()
            )
        )

        assert (http_response.status_code, json.loads(http_response.body)) == (201, {"run_id": "run-1"})
        assert fake_drafting_client.open_run_requests == [
            client.OpenRunRequest(job="Plan a trip")
        ]

    async def test_open_run_missing_a_field_is_a_bad_request_that_calls_nothing(self) -> None:
        fake_drafting_client = FakeDraftingClient()

        with pytest.raises(protocol.BadRequest):
            await handlers.HttpHandler(fake_drafting_client).open_run(protocol.HttpRequest(path_params={}, body=b"{}"))

        assert fake_drafting_client.open_run_requests == []

    async def test_get_run_answers_the_fields_it_reads_for_the_run_id_in_the_path(self) -> None:
        fake_drafting_client = FakeDraftingClient()

        http_response = await handlers.HttpHandler(fake_drafting_client).get_run(
            protocol.HttpRequest(path_params={"run_id": "run-1"}, body=b"")
        )

        assert (http_response.status_code, json.loads(http_response.body)) == (
            200,
            {"run_id": "run-1", "job": "Plan a trip"},
        )
        assert fake_drafting_client.get_run_requests == [client.GetRunRequest(run_id="run-1")]

    async def test_get_run_without_a_run_id_is_a_bad_request_that_calls_nothing(self) -> None:
        fake_drafting_client = FakeDraftingClient()

        with pytest.raises(protocol.BadRequest):
            await handlers.HttpHandler(fake_drafting_client).get_run(protocol.HttpRequest(path_params={}, body=b""))

        assert fake_drafting_client.get_run_requests == []
