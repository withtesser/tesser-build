from __future__ import annotations

import json

import tesser.srv as ts


class BadRequest(ts.Rejection):
    pass


class HttpRequest(ts.Request):

    def __init__(self, body: bytes, parameters: dict[str, str]) -> None:
        super().__init__(body=body, parameters=parameters)

    body: bytes
    parameters: dict[str, str]

    def text(self, name: str) -> str:
        try:
            data = json.loads(self.body)
        except ValueError as e:
            raise BadRequest(f"malformed JSON: {e}") from e
        if not isinstance(data, dict):
            raise BadRequest("expected a JSON object")
        value = data.get(name)
        if not isinstance(value, str):
            raise BadRequest(f"{name} must be a string")
        return value

    def parameter(self, name: str) -> str:
        value = self.parameters.get(name)
        if value is None:
            raise BadRequest(f"{name} is missing from the path")
        return value


class HttpResponse(ts.Response):

    def __init__(self, status_code: int, body: bytes) -> None:
        super().__init__(status_code=status_code, body=body)

    status_code: int
    body: bytes

    @classmethod
    def problem(cls, status_code: int, detail: str) -> HttpResponse:
        return cls(status_code=status_code, body=json.dumps({"detail": detail}).encode())
