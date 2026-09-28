from __future__ import annotations

import typing

import tesser.context as ts


class OpenRunRequest(ts.Request):

    def __init__(self, job: str) -> None:
        self.job = job


class OpenRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class Run(ts.Response):

    def __init__(self, run_id: str, job: str, stage: str) -> None:
        self.run_id = run_id
        self.job = job
        self.stage = stage


class GetRunRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class GetRunResponse(ts.Response):

    def __init__(self, runs: tuple[Run, ...]) -> None:
        self.runs = runs


class DraftingClient(ts.Client, typing.Protocol):

    async def open_run(self, open_run_request: OpenRunRequest) -> OpenRunResponse: ...

    async def get_run(self, get_run_request: GetRunRequest) -> GetRunResponse: ...
