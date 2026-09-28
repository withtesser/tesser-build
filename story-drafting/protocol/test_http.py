from __future__ import annotations

import json

import pytest

import protocol as protocol


class TestHttpRequest:

    def test_a_string_field_is_read_from_the_body(self) -> None:
        http_request = protocol.HttpRequest(body=b'{"job": "a job"}', parameters={})
        assert http_request.text("job") == "a job"

    def test_a_path_parameter_is_read_by_its_name(self) -> None:
        http_request = protocol.HttpRequest(body=b"", parameters={"run_id": "r1"})
        assert http_request.parameter("run_id") == "r1"

    def test_a_missing_path_parameter_is_a_bad_request(self) -> None:
        http_request = protocol.HttpRequest(body=b"", parameters={})
        with pytest.raises(protocol.BadRequest):
            http_request.parameter("run_id")

    def test_a_missing_field_is_a_bad_request(self) -> None:
        http_request = protocol.HttpRequest(body=b"{}", parameters={})
        with pytest.raises(protocol.BadRequest):
            http_request.text("job")

    def test_a_non_string_field_is_a_bad_request(self) -> None:
        http_request = protocol.HttpRequest(body=b'{"job": 1}', parameters={})
        with pytest.raises(protocol.BadRequest):
            http_request.text("job")

    def test_malformed_json_is_a_bad_request(self) -> None:
        http_request = protocol.HttpRequest(body=b"{", parameters={})
        with pytest.raises(protocol.BadRequest):
            http_request.text("job")

    def test_a_non_object_body_is_a_bad_request(self) -> None:
        http_request = protocol.HttpRequest(body=b"[]", parameters={})
        with pytest.raises(protocol.BadRequest):
            http_request.text("job")


class TestHttpResponse:

    def test_a_problem_carries_its_status_and_a_json_detail(self) -> None:
        http_response = protocol.HttpResponse.problem(404, "no run has that id")
        assert http_response.status_code == 404
        assert json.loads(http_response.body) == {"detail": "no run has that id"}
