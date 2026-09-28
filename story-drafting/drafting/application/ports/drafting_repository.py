from __future__ import annotations

import enum
import typing

import tesser.application as ts


class LoadDraftingOutcome(enum.Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"


class StoryRow(ts.Response):

    def __init__(self, story_id: str, text: str) -> None:
        self.story_id = story_id
        self.text = text


class DraftingRow(ts.Response):

    def __init__(
        self, drafting_id: str, job: str, step: str, stories: tuple[StoryRow, ...], accepted_stories: tuple[StoryRow, ...]
    ) -> None:
        self.drafting_id = drafting_id
        self.job = job
        self.step = step
        self.stories = stories
        self.accepted_stories = accepted_stories


class IssueDraftingIdRequest(ts.Request):

    def __init__(self) -> None:
        return None


class IssueDraftingIdResponse(ts.Response):

    def __init__(self, drafting_id: str) -> None:
        self.drafting_id = drafting_id


class SaveDraftingRequest(ts.Request):

    def __init__(self, drafting_row: DraftingRow) -> None:
        self.drafting_row = drafting_row


class SaveDraftingResponse(ts.Response):

    def __init__(self, drafting_id: str) -> None:
        self.drafting_id = drafting_id


class LoadDraftingRequest(ts.Request):

    def __init__(self, drafting_id: str) -> None:
        self.drafting_id = drafting_id


class LoadDraftingResponse(ts.Response):

    def __init__(self, outcome: LoadDraftingOutcome, drafting_rows: tuple[DraftingRow, ...]) -> None:
        self.outcome = outcome
        self.drafting_rows = drafting_rows


class DraftingRepository(ts.Port, typing.Protocol):

    async def issue_drafting_id(self, issue_drafting_id_request: IssueDraftingIdRequest) -> IssueDraftingIdResponse: ...

    async def save_drafting(self, save_drafting_request: SaveDraftingRequest) -> SaveDraftingResponse: ...

    async def load_drafting(self, load_drafting_request: LoadDraftingRequest) -> LoadDraftingResponse: ...


class DraftingStore(ts.Store, typing.Protocol):

    def transaction(self) -> typing.AsyncContextManager[DraftingRepository]: ...
