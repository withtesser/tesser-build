from __future__ import annotations

import typing

import tesser.context as ts


class OpenRunRequest(ts.Request):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class OpenRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class GetRunRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class GetRunResponse(ts.Response):

    def __init__(
        self,
        run_id: str,
        job: str,
        stage: str,
        stories: tuple[str, ...],
        accepted_stories: tuple[str, ...],
    ) -> None:
        self.run_id = run_id
        self.job = job
        self.stage = stage
        self.stories = stories
        self.accepted_stories = accepted_stories


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
