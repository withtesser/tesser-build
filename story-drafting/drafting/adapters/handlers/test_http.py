from __future__ import annotations

import json

import tesser.testing as ts

import drafting.adapters.handlers as handlers
import drafting.client as client
import protocol as protocol


@ts.fake
class FakeDraftingClient(client.DraftingClient):

    def __init__(self) -> None:
        self.begun: list[client.BeginRunRequest] = []

    async def begin_run(self, begin_run_request: client.BeginRunRequest) -> client.BeginRunResponse:
        self.begun.append(begin_run_request)
        return client.BeginRunResponse(run_id=begin_run_request.run_id)

    async def get_run(self, get_run_request: client.GetRunRequest) -> client.GetRunResponse:
        return client.GetRunResponse(
            run_id=get_run_request.run_id,
            job="a job",
            stage="drafting",
            stories=(client.Story(text="a story"),),
            accepted_stories=(),
        )


@ts.fake
class FakeRefusingDraftingClient(client.DraftingClient):

    def __init__(self, error: Exception) -> None:
        self.error = error

    async def begin_run(self, begin_run_request: client.BeginRunRequest) -> client.BeginRunResponse:
        raise self.error

    async def get_run(self, get_run_request: client.GetRunRequest) -> client.GetRunResponse:
        raise self.error


class TestHandler:

    async def test_beginning_a_run_answers_202_with_its_id(self) -> None:
        fake_drafting_client = FakeDraftingClient()
        http_response = await handlers.Handler(fake_drafting_client).begin_run(
            protocol.HttpRequest(body=b'{"run_id": "r1", "job": "a job"}', parameters={})
        )
        assert http_response.status_code == 202
        assert json.loads(http_response.body) == {"run_id": "r1"}
        assert fake_drafting_client.begun == [client.BeginRunRequest(run_id="r1", job="a job")]

    async def test_reading_a_run_answers_200_with_the_run(self) -> None:
        http_response = await handlers.Handler(FakeDraftingClient()).get_run(
            protocol.HttpRequest(body=b"", parameters={"run_id": "r1"})
        )
        assert http_response.status_code == 200
        assert json.loads(http_response.body) == {
            "run_id": "r1",
            "job": "a job",
            "stage": "drafting",
            "stories": [{"text": "a story"}],
            "accepted_stories": [],
        }

    async def test_a_rejected_run_answers_422(self) -> None:
        http_response = await handlers.Handler(
            FakeRefusingDraftingClient(client.RunRejected("empty_job", "a job to be done is never empty"))
        ).begin_run(protocol.HttpRequest(body=b'{"run_id": "r1", "job": ""}', parameters={}))
        assert http_response.status_code == 422
        assert json.loads(http_response.body) == {"detail": "a job to be done is never empty"}

    async def test_a_run_not_found_answers_404(self) -> None:
        http_response = await handlers.Handler(FakeRefusingDraftingClient(client.RunNotFound("no run has that id"))).get_run(
            protocol.HttpRequest(body=b"", parameters={"run_id": "r1"})
        )
        assert http_response.status_code == 404
        assert json.loads(http_response.body) == {"detail": "no run has that id"}
