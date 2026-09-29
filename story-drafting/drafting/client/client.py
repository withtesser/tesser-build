from __future__ import annotations

import typing

import tesser.context as ts


class BeginRunRequest(ts.Request):

    def __init__(self, job: str) -> None:
        self.job = job


class BeginRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class Run(ts.Response):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class GetRunRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class GetRunResponse(ts.Response):

    def __init__(self, run: Run) -> None:
        self.run = run


class DraftingClient(ts.Client, typing.Protocol):

    async def begin_run(self, begin_run_request: BeginRunRequest) -> BeginRunResponse: ...

    async def get_run(self, get_run_request: GetRunRequest) -> GetRunResponse: ...
