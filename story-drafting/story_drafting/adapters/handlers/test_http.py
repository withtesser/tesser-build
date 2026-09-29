from __future__ import annotations

import json

import pytest
import tesser.testing as ts

import story_drafting.adapters.handlers as handlers
import story_drafting.client as client
import protocol


@ts.fake
class FakeStoryDraftingClient(client.StoryDraftingClient):

    def __init__(self) -> None:
        self.submit_jtbd_requests: list[client.SubmitJtbdRequest] = []
        self.check_status_requests: list[client.CheckStatusRequest] = []

    async def submit_jtbd(self, submit_jtbd_request: client.SubmitJtbdRequest) -> client.SubmitJtbdResponse:
        self.submit_jtbd_requests.append(submit_jtbd_request)
        return client.SubmitJtbdResponse(jtbd_id="jtbd-1")

    async def check_status(self, check_status_request: client.CheckStatusRequest) -> client.CheckStatusResponse:
        self.check_status_requests.append(check_status_request)
        return client.CheckStatusResponse(client.Jtbd(jtbd_id="jtbd-1", job="Design a billing page, get my sign-off, then build it"))


class TestHttpHandler:

    async def test_submit_jtbd_passes_each_body_field_as_its_field_and_answers_the_jtbd_id(self) -> None:
        fake_story_drafting_client = FakeStoryDraftingClient()

        http_response = await handlers.HttpHandler(fake_story_drafting_client).submit_jtbd(
            protocol.HttpRequest(
                path_params={}, body=json.dumps({"job": "Design a billing page, get my sign-off, then build it"}).encode()
            )
        )

        assert (http_response.status_code, json.loads(http_response.body)) == (201, {"jtbd_id": "jtbd-1"})
        assert fake_story_drafting_client.submit_jtbd_requests == [
            client.SubmitJtbdRequest(job="Design a billing page, get my sign-off, then build it")
        ]

    async def test_submit_jtbd_missing_a_field_is_a_bad_request_that_calls_nothing(self) -> None:
        fake_story_drafting_client = FakeStoryDraftingClient()

        with pytest.raises(protocol.BadRequest):
            await handlers.HttpHandler(fake_story_drafting_client).submit_jtbd(protocol.HttpRequest(path_params={}, body=b"{}"))

        assert fake_story_drafting_client.submit_jtbd_requests == []

    async def test_check_status_answers_the_fields_it_reads_for_the_jtbd_id_in_the_path(self) -> None:
        fake_story_drafting_client = FakeStoryDraftingClient()

        http_response = await handlers.HttpHandler(fake_story_drafting_client).check_status(
            protocol.HttpRequest(path_params={"jtbd_id": "jtbd-1"}, body=b"")
        )

        assert (http_response.status_code, json.loads(http_response.body)) == (
            200,
            {"jtbd_id": "jtbd-1", "job": "Design a billing page, get my sign-off, then build it"},
        )
        assert fake_story_drafting_client.check_status_requests == [client.CheckStatusRequest(jtbd_id="jtbd-1")]

    async def test_check_status_without_a_jtbd_id_is_a_bad_request_that_calls_nothing(self) -> None:
        fake_story_drafting_client = FakeStoryDraftingClient()

        with pytest.raises(protocol.BadRequest):
            await handlers.HttpHandler(fake_story_drafting_client).check_status(protocol.HttpRequest(path_params={}, body=b""))

        assert fake_story_drafting_client.check_status_requests == []
