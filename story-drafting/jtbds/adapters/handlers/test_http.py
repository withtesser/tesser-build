from __future__ import annotations

import json

import pytest
import tesser.testing as ts

import jtbds.adapters.handlers as handlers
import jtbds.client as client
import protocol


@ts.fake
class FakeJtbdsClient(client.JtbdsClient):

    def __init__(self) -> None:
        self.submit_jtbd_requests: list[client.SubmitJtbdRequest] = []
        self.get_jtbd_requests: list[client.GetJtbdRequest] = []

    async def submit_jtbd(self, submit_jtbd_request: client.SubmitJtbdRequest) -> client.SubmitJtbdResponse:
        self.submit_jtbd_requests.append(submit_jtbd_request)
        return client.SubmitJtbdResponse(jtbd_id="jtbd-1")

    async def get_jtbd(self, get_jtbd_request: client.GetJtbdRequest) -> client.GetJtbdResponse:
        self.get_jtbd_requests.append(get_jtbd_request)
        return client.GetJtbdResponse(client.Jtbd(jtbd_id="jtbd-1", job="Design a login page, get my sign-off, then build it", step="drafting", draft_count=0, picked_draft="none"))


class TestHttpHandler:

    async def test_submit_jtbd_passes_the_job_at_drafting_with_no_drafts_and_answers_the_jtbd_id(self) -> None:
        fake_jtbds_client = FakeJtbdsClient()

        http_response = await handlers.HttpHandler(fake_jtbds_client).submit_jtbd(
            protocol.HttpRequest(
                path_params={}, body=json.dumps({"job": "Design a login page, get my sign-off, then build it"}).encode()
            )
        )

        assert (http_response.status_code, json.loads(http_response.body)) == (201, {"jtbd_id": "jtbd-1"})
        assert fake_jtbds_client.submit_jtbd_requests == [
            client.SubmitJtbdRequest(job="Design a login page, get my sign-off, then build it", step="drafting", draft_count=0, picked_draft="")
        ]

    async def test_submit_jtbd_missing_a_field_is_a_bad_request_that_calls_nothing(self) -> None:
        fake_jtbds_client = FakeJtbdsClient()

        with pytest.raises(protocol.BadRequest):
            await handlers.HttpHandler(fake_jtbds_client).submit_jtbd(protocol.HttpRequest(path_params={}, body=b"{}"))

        assert fake_jtbds_client.submit_jtbd_requests == []

    async def test_get_jtbd_answers_the_fields_it_reads_for_the_jtbd_id_in_the_path(self) -> None:
        fake_jtbds_client = FakeJtbdsClient()

        http_response = await handlers.HttpHandler(fake_jtbds_client).get_jtbd(
            protocol.HttpRequest(path_params={"jtbd_id": "jtbd-1"}, body=b"")
        )

        assert (http_response.status_code, json.loads(http_response.body)) == (
            200,
            {"jtbd_id": "jtbd-1", "job": "Design a login page, get my sign-off, then build it", "step": "drafting", "draft_count": 0, "picked_draft": "none"},
        )
        assert fake_jtbds_client.get_jtbd_requests == [client.GetJtbdRequest(jtbd_id="jtbd-1")]

    async def test_get_jtbd_without_a_jtbd_id_is_a_bad_request_that_calls_nothing(self) -> None:
        fake_jtbds_client = FakeJtbdsClient()

        with pytest.raises(protocol.BadRequest):
            await handlers.HttpHandler(fake_jtbds_client).get_jtbd(protocol.HttpRequest(path_params={}, body=b""))

        assert fake_jtbds_client.get_jtbd_requests == []
