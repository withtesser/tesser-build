from __future__ import annotations

import enum
import typing

import tesser.application as ts


class SaveRunRequest(ts.Request):

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


class SaveRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class LoadRunRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class LoadRunOutcome(enum.Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"


class RunRecord(ts.Response):

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


class LoadRunResponse(ts.Response):

    def __init__(self, outcome: LoadRunOutcome, runs: tuple[RunRecord, ...]) -> None:
        self.outcome = outcome
        self.runs = runs


class RunRepository(ts.Port, typing.Protocol):

    async def save_run(self, save_run_request: SaveRunRequest) -> SaveRunResponse: ...

    async def load_run(self, load_run_request: LoadRunRequest) -> LoadRunResponse: ...


class RunStore(ts.Store, typing.Protocol):

    def transaction(self) -> typing.AsyncContextManager[RunRepository]: ...
