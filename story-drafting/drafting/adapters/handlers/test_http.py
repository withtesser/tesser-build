from __future__ import annotations

import json

import pytest
import tesser.testing as ts

import drafting.adapters.handlers as handlers
import drafting.client as client
import protocol as protocol


@ts.fake
class FakeDraftingClient(client.DraftingClient):

    def __init__(self, runs: tuple[client.Run, ...]) -> None:
        self.opened: list[client.OpenRunRequest] = []
        self.got: list[client.GetRunRequest] = []
        self._runs = runs

    async def open_run(self, open_run_request: client.OpenRunRequest) -> client.OpenRunResponse:
        self.opened.append(open_run_request)
        return client.OpenRunResponse(run_id="run-1")

    async def get_run(self, get_run_request: client.GetRunRequest) -> client.GetRunResponse:
        self.got.append(get_run_request)
        return client.GetRunResponse(runs=self._runs)


class TestHttpHandler:

    async def test_opening_a_run_is_accepted_with_its_run_id(self) -> None:
        http_handler = handlers.HttpHandler(FakeDraftingClient(runs=()))

        http_response = await http_handler.open_run(
            protocol.HttpRequest(path_params=(), body=b'{"job": "plan a migration"}')
        )

        assert http_response.status_code == 202
        assert json.loads(http_response.body) == {"run_id": "run-1"}

    async def test_opening_a_run_carries_the_job_to_the_client(self) -> None:
        fake_drafting_client = FakeDraftingClient(runs=())

        await handlers.HttpHandler(fake_drafting_client).open_run(
            protocol.HttpRequest(path_params=(), body=b'{"job": "plan a migration"}')
        )

        assert [opened.job for opened in fake_drafting_client.opened] == ["plan a migration"]

    async def test_opening_a_run_without_a_job_is_a_bad_request(self) -> None:
        http_handler = handlers.HttpHandler(FakeDraftingClient(runs=()))

        with pytest.raises(protocol.BadRequest):
            await http_handler.open_run(protocol.HttpRequest(path_params=(), body=b"{}"))

    async def test_a_run_reads_back_as_its_fields(self) -> None:
        fake_drafting_client = FakeDraftingClient(
            runs=(client.Run(run_id="run-1", job="plan a migration", stage="drafting"),)
        )

        http_response = await handlers.HttpHandler(fake_drafting_client).get_run(
            protocol.HttpRequest(path_params=(("run_id", "run-1"),), body=b"")
        )

        assert http_response.status_code == 200
        assert json.loads(http_response.body) == {"run_id": "run-1", "job": "plan a migration", "stage": "drafting"}
        assert [got.run_id for got in fake_drafting_client.got] == ["run-1"]

    async def test_a_run_the_client_does_not_have_is_404(self) -> None:
        http_response = await handlers.HttpHandler(FakeDraftingClient(runs=())).get_run(
            protocol.HttpRequest(path_params=(("run_id", "run-9"),), body=b"")
        )

        assert http_response.status_code == 404
        assert json.loads(http_response.body) == {"detail": "no run run-9"}
