# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import collections.abc as collections_abc
import json

import tesser.srv as ts


class BadRequest(ts.Rejection):
    pass


class HttpRequest(ts.Request):

    def __init__(self, path_params: collections_abc.Mapping[str, str], body: bytes) -> None:
        super().__init__(path_params=dict(path_params), body=body)

    path_params: collections_abc.Mapping[str, str]
    body: bytes

    def text(self, name: str) -> str:
        try:
            data = json.loads(self.body)
        except ValueError as error:
            raise BadRequest(f"malformed JSON: {error}") from error
        if not isinstance(data, dict):
            raise BadRequest("expected a JSON object")
        value = data.get(name)
        if not isinstance(value, str):
            raise BadRequest(f"{name} must be a string")
        return value

    def integer(self, name: str) -> int:
        try:
            data = json.loads(self.body)
        except ValueError as error:
            raise BadRequest(f"malformed JSON: {error}") from error
        if not isinstance(data, dict):
            raise BadRequest("expected a JSON object")
        value = data.get(name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise BadRequest(f"{name} must be an integer")
        return value

    def path_param(self, name: str) -> str:
        value = self.path_params.get(name)
        if not value:
            raise BadRequest(f"missing path parameter: {name}")
        return value


class HttpResponse(ts.Response):

    def __init__(self, status_code: int, body: bytes) -> None:
        super().__init__(status_code=status_code, body=body)

    status_code: int
    body: bytes

    @classmethod
    def problem(cls, status_code: int, detail: str) -> HttpResponse:
        return cls(status_code=status_code, body=json.dumps({"detail": detail}).encode())
