# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import json

import pytest

import protocol


class TestHttpRequest:

    def test_a_string_field_is_read_from_the_body(self) -> None:
        http_request = protocol.HttpRequest(path_params={}, body=b'{"name": "Ada"}')

        assert http_request.text("name") == "Ada"

    def test_an_integer_field_is_read_from_the_body(self) -> None:
        http_request = protocol.HttpRequest(path_params={}, body=b'{"count": -13}')

        assert http_request.integer("count") == -13

    def test_a_missing_field_is_a_bad_request(self) -> None:
        with pytest.raises(protocol.BadRequest) as raised:
            protocol.HttpRequest(path_params={}, body=b"{}").text("name")

        assert str(raised.value) == "name must be a string"

    def test_a_field_of_the_wrong_type_is_a_bad_request(self) -> None:
        with pytest.raises(protocol.BadRequest) as raised:
            protocol.HttpRequest(path_params={}, body=b'{"count": "three"}').integer("count")

        assert str(raised.value) == "count must be an integer"

    def test_a_boolean_is_not_an_integer(self) -> None:
        with pytest.raises(protocol.BadRequest):
            protocol.HttpRequest(path_params={}, body=b'{"count": true}').integer("count")

    def test_malformed_json_is_a_bad_request(self) -> None:
        with pytest.raises(protocol.BadRequest):
            protocol.HttpRequest(path_params={}, body=b"{").text("name")

    def test_a_body_that_is_not_an_object_is_a_bad_request(self) -> None:
        with pytest.raises(protocol.BadRequest) as raised:
            protocol.HttpRequest(path_params={}, body=b"[]").text("name")

        assert str(raised.value) == "expected a JSON object"

    def test_a_path_parameter_is_read_by_its_name(self) -> None:
        http_request = protocol.HttpRequest(path_params={"id": "id-1"}, body=b"")

        assert http_request.path_param("id") == "id-1"

    def test_a_missing_path_parameter_is_a_bad_request(self) -> None:
        with pytest.raises(protocol.BadRequest):
            protocol.HttpRequest(path_params={}, body=b"").path_param("id")

    def test_an_integer_path_parameter_is_read_as_an_integer(self) -> None:
        http_request = protocol.HttpRequest(path_params={"copies": "12"}, body=b"")

        assert http_request.integer_path_param("copies") == 12

    def test_an_integer_path_parameter_that_is_not_digits_is_a_bad_request(self) -> None:
        with pytest.raises(protocol.BadRequest) as raised:
            protocol.HttpRequest(path_params={"copies": "twelve"}, body=b"").integer_path_param("copies")

        assert str(raised.value) == "path parameter copies must be an integer"

    def test_a_missing_integer_path_parameter_is_a_bad_request(self) -> None:
        with pytest.raises(protocol.BadRequest):
            protocol.HttpRequest(path_params={}, body=b"").integer_path_param("copies")

    def test_two_requests_with_the_same_fields_are_equal(self) -> None:
        assert protocol.HttpRequest(path_params={}, body=b"{}") == protocol.HttpRequest(path_params={}, body=b"{}")
        assert protocol.HttpRequest(path_params={}, body=b"{}") != protocol.HttpRequest(path_params={}, body=b"[]")


class TestHttpResponse:

    def test_a_problem_carries_its_status_and_a_json_detail(self) -> None:
        http_response = protocol.HttpResponse.problem(404, "not found")

        assert http_response.status_code == 404
        assert json.loads(http_response.body) == {"detail": "not found"}

    def test_two_responses_with_the_same_fields_are_equal(self) -> None:
        assert protocol.HttpResponse(200, b"{}") == protocol.HttpResponse(200, b"{}")
        assert protocol.HttpResponse(200, b"{}") != protocol.HttpResponse(201, b"{}")
