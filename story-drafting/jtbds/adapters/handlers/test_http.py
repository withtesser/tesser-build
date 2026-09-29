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
        self.check_jtbd_status_requests: list[client.CheckJtbdStatusRequest] = []

    async def submit_jtbd(self, submit_jtbd_request: client.SubmitJtbdRequest) -> client.SubmitJtbdResponse:
        self.submit_jtbd_requests.append(submit_jtbd_request)
        return client.SubmitJtbdResponse(jtbd_id="jtbd-1")

    async def check_jtbd_status(self, check_jtbd_status_request: client.CheckJtbdStatusRequest) -> client.CheckJtbdStatusResponse:
        self.check_jtbd_status_requests.append(check_jtbd_status_request)
        return client.CheckJtbdStatusResponse(client.Jtbd(jtbd_id="jtbd-1", status="drafting"))


class TestHttpHandler:

    async def test_submit_jtbd_passes_each_body_field_as_its_field_and_answers_the_jtbd_id(self) -> None:
        fake_jtbds_client = FakeJtbdsClient()

        http_response = await handlers.HttpHandler(fake_jtbds_client).submit_jtbd(
            protocol.HttpRequest(
                path_params={}, body=json.dumps({"description": "design the dashboard", "status": "drafting"}).encode()
            )
        )

        assert (http_response.status_code, json.loads(http_response.body)) == (201, {"jtbd_id": "jtbd-1"})
        assert fake_jtbds_client.submit_jtbd_requests == [
            client.SubmitJtbdRequest(description="design the dashboard", status="drafting")
        ]

    async def test_submit_jtbd_missing_a_field_is_a_bad_request_that_calls_nothing(self) -> None:
        fake_jtbds_client = FakeJtbdsClient()

        with pytest.raises(protocol.BadRequest):
            await handlers.HttpHandler(fake_jtbds_client).submit_jtbd(protocol.HttpRequest(path_params={}, body=b"{}"))

        assert fake_jtbds_client.submit_jtbd_requests == []

    async def test_check_jtbd_status_answers_the_fields_it_reads_for_the_jtbd_id_in_the_path(self) -> None:
        fake_jtbds_client = FakeJtbdsClient()

        http_response = await handlers.HttpHandler(fake_jtbds_client).check_jtbd_status(
            protocol.HttpRequest(path_params={"jtbd_id": "jtbd-1"}, body=b"")
        )

        assert (http_response.status_code, json.loads(http_response.body)) == (
            200,
            {"jtbd_id": "jtbd-1", "status": "drafting"},
        )
        assert fake_jtbds_client.check_jtbd_status_requests == [client.CheckJtbdStatusRequest(jtbd_id="jtbd-1")]

    async def test_check_jtbd_status_without_a_jtbd_id_is_a_bad_request_that_calls_nothing(self) -> None:
        fake_jtbds_client = FakeJtbdsClient()

        with pytest.raises(protocol.BadRequest):
            await handlers.HttpHandler(fake_jtbds_client).check_jtbd_status(protocol.HttpRequest(path_params={}, body=b""))

        assert fake_jtbds_client.check_jtbd_status_requests == []
