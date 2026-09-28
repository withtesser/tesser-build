from __future__ import annotations

import json

import pytest

import protocol as protocol


class TestHttpRequest:

    def test_a_string_field_is_read_from_the_body(self) -> None:
        http_request = protocol.HttpRequest(path_params=(), body=b'{"job": "plan a migration"}')

        assert http_request.text("job") == "plan a migration"

    def test_a_path_param_is_read_by_its_name(self) -> None:
        http_request = protocol.HttpRequest(path_params=(("run_id", "run-1"),), body=b"")

        assert http_request.path_param("run_id") == "run-1"

    def test_a_missing_path_param_is_a_bad_request(self) -> None:
        http_request = protocol.HttpRequest(path_params=(), body=b"")

        with pytest.raises(protocol.BadRequest):
            http_request.path_param("run_id")

    def test_a_missing_field_is_a_bad_request(self) -> None:
        http_request = protocol.HttpRequest(path_params=(), body=b"{}")

        with pytest.raises(protocol.BadRequest):
            http_request.text("job")

    def test_a_field_that_is_not_a_string_is_a_bad_request(self) -> None:
        http_request = protocol.HttpRequest(path_params=(), body=b'{"job": 7}')

        with pytest.raises(protocol.BadRequest):
            http_request.text("job")

    def test_malformed_json_is_a_bad_request(self) -> None:
        http_request = protocol.HttpRequest(path_params=(), body=b"{")

        with pytest.raises(protocol.BadRequest):
            http_request.text("job")

    def test_a_non_object_body_is_a_bad_request(self) -> None:
        http_request = protocol.HttpRequest(path_params=(), body=b"[]")

        with pytest.raises(protocol.BadRequest):
            http_request.text("job")


class TestHttpResponse:

    def test_a_problem_carries_its_status_and_a_json_detail(self) -> None:
        http_response = protocol.HttpResponse.problem(404, "no run run-9")

        assert http_response.status_code == 404
        assert json.loads(http_response.body) == {"detail": "no run run-9"}
