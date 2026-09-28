from __future__ import annotations

import typing

import tesser.context as ts


class BeginRunRequest(ts.Request):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class BeginRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class GetRunRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class Story(ts.Response):

    def __init__(self, text: str) -> None:
        self.text = text


class GetRunResponse(ts.Response):

    def __init__(
        self,
        run_id: str,
        job: str,
        stage: str,
        stories: tuple[Story, ...],
        accepted_stories: tuple[Story, ...],
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

    async def begin_run(self, begin_run_request: BeginRunRequest) -> BeginRunResponse: ...

    async def get_run(self, get_run_request: GetRunRequest) -> GetRunResponse: ...
