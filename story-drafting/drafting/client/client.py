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

    def __init__(
        self,
        run_id: str,
        job: str,
        step: str,
        drafted_stories: tuple[str, ...],
        accepted_stories: tuple[str, ...],
    ) -> None:
        self.run_id = run_id
        self.job = job
        self.step = step
        self.drafted_stories = drafted_stories
        self.accepted_stories = accepted_stories


class GetRunRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class GetRunResponse(ts.Response):

    def __init__(self, run: Run) -> None:
        self.run = run


class RunRejected(ts.Error):

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class RunNotFound(ts.Error):

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


ERRORS: typing.Final[tuple[type[RunRejected], type[RunNotFound]]] = (RunRejected, RunNotFound)


class DraftingClient(ts.Client, typing.Protocol):

    async def open_run(self, open_run_request: OpenRunRequest) -> OpenRunResponse: ...

    async def get_run(self, get_run_request: GetRunRequest) -> GetRunResponse: ...
