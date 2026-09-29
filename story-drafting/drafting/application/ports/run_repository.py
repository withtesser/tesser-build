from __future__ import annotations

import typing

import tesser.application as ts


class Run(ts.Response):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class SaveRunRequest(ts.Request):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class SaveRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class LoadRunRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class LoadRunResponse(ts.Response):

    def __init__(self, runs: tuple[Run, ...]) -> None:
        self.runs = runs


class RunRepository(ts.Port, typing.Protocol):

    async def save_run(self, save_run_request: SaveRunRequest) -> SaveRunResponse: ...

    async def load_run(self, load_run_request: LoadRunRequest) -> LoadRunResponse: ...


class RunStore(ts.Store, typing.Protocol):

    def transaction(self) -> typing.AsyncContextManager[RunRepository]: ...
