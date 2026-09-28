from __future__ import annotations

import enum
import typing

import tesser.application as ts


class SaveRunRequest(ts.Request):

    def __init__(self, run_id: str, job: str, stage: str) -> None:
        self.run_id = run_id
        self.job = job
        self.stage = stage


class SaveRunResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class GetRunRequest(ts.Request):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class GetRunOutcome(enum.Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"


class DraftedStory(ts.Response):

    def __init__(self, text: str) -> None:
        self.text = text


class RunRecord(ts.Response):

    def __init__(
        self,
        run_id: str,
        job: str,
        stage: str,
        stories: tuple[DraftedStory, ...],
        accepted_stories: tuple[DraftedStory, ...],
    ) -> None:
        self.run_id = run_id
        self.job = job
        self.stage = stage
        self.stories = stories
        self.accepted_stories = accepted_stories


class GetRunResponse(ts.Response):

    def __init__(self, outcome: GetRunOutcome, runs: tuple[RunRecord, ...]) -> None:
        self.outcome = outcome
        self.runs = runs


class RunRepository(ts.Port, typing.Protocol):

    async def save_run(self, save_run_request: SaveRunRequest) -> SaveRunResponse: ...

    async def get_run(self, get_run_request: GetRunRequest) -> GetRunResponse: ...
