from __future__ import annotations

import json

import pytest
import tesser.testing as ts

import drafting.adapters.handlers as handlers
import drafting.client as client
import protocol as protocol


@ts.fake
class FakeDraftingClient(client.DraftingClient):

    def __init__(self) -> None:
        self.opened: list[tuple[str, str]] = []
        self.read: list[str] = []

    async def open_run(self, open_run_request: client.OpenRunRequest) -> client.OpenRunResponse:
        self.opened.append((open_run_request.run_id, open_run_request.job))
        return client.OpenRunResponse(run_id=open_run_request.run_id)

    async def get_run(self, get_run_request: client.GetRunRequest) -> client.GetRunResponse:
        self.read.append(get_run_request.run_id)
        return client.GetRunResponse(
            run_id=get_run_request.run_id, job="ship", stage="awaiting_pick", stories=("a", "b"), accepted_stories=()
        )


@ts.fake
class FakeRefusingDraftingClient(client.DraftingClient):

    def __init__(self, error: Exception) -> None:
        self.error = error

    async def open_run(self, open_run_request: client.OpenRunRequest) -> client.OpenRunResponse:
        raise self.error

    async def get_run(self, get_run_request: client.GetRunRequest) -> client.GetRunResponse:
        raise self.error


class TestHandler:

    async def test_an_opened_run_is_accepted_with_its_id_and_carries_the_body_to_the_client(self) -> None:
        fake_drafting_client = FakeDraftingClient()
        http_response = await handlers.Handler(fake_drafting_client).open_run(
            protocol.HttpRequest(path_params={}, body=b'{"run_id": "r1", "job": "ship"}')
        )
        assert http_response.status_code == 202
        assert json.loads(http_response.body) == {"run_id": "r1"}
        assert fake_drafting_client.opened == [("r1", "ship")]

    async def test_a_missing_job_is_a_bad_request(self) -> None:
        with pytest.raises(protocol.BadRequest):
            await handlers.Handler(FakeDraftingClient()).open_run(
                protocol.HttpRequest(path_params={}, body=b'{"run_id": "r1"}')
            )

    async def test_a_run_is_read_by_the_id_in_its_path(self) -> None:
        fake_drafting_client = FakeDraftingClient()
        http_response = await handlers.Handler(fake_drafting_client).get_run(
            protocol.HttpRequest(path_params={"run_id": "r1"}, body=b"")
        )
        assert http_response.status_code == 200
        assert json.loads(http_response.body) == {
            "run_id": "r1",
            "job": "ship",
            "stage": "awaiting_pick",
            "stories": ["a", "b"],
            "accepted_stories": [],
        }
        assert fake_drafting_client.read == ["r1"]

    async def test_a_rejected_run_is_422_carrying_the_contexts_wording(self) -> None:
        http_response = await handlers.Handler(
            FakeRefusingDraftingClient(client.RunRejected("empty_job", "a job to be done is never blank"))
        ).open_run(protocol.HttpRequest(path_params={}, body=b'{"run_id": "r1", "job": " "}'))
        assert http_response.status_code == 422
        assert json.loads(http_response.body) == {"detail": "a job to be done is never blank"}

    async def test_a_run_not_found_is_404_carrying_the_contexts_wording(self) -> None:
        http_response = await handlers.Handler(FakeRefusingDraftingClient(client.RunNotFound("no run 'r1'"))).get_run(
            protocol.HttpRequest(path_params={"run_id": "r1"}, body=b"")
        )
        assert http_response.status_code == 404
        assert json.loads(http_response.body) == {"detail": "no run 'r1'"}

    async def test_a_failure_the_context_never_declared_leaves_the_handler(self) -> None:
        with pytest.raises(RuntimeError):
            await handlers.Handler(FakeRefusingDraftingClient(RuntimeError("unexpected"))).get_run(
                protocol.HttpRequest(path_params={"run_id": "r1"}, body=b"")
            )
