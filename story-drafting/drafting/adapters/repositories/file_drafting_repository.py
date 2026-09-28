from __future__ import annotations

import contextlib
import json
import os
import pathlib
import typing
import uuid

import tesser.adapters as ts

import drafting.application.ports as ports

_SUFFIX: typing.Final[str] = ".json"


class FileDraftingRepository(ts.Repository):

    def __init__(self, directory: pathlib.Path) -> None:
        self._directory = directory

    async def issue_drafting_id(
        self, issue_drafting_id_request: ports.IssueDraftingIdRequest
    ) -> ports.IssueDraftingIdResponse:
        return ports.IssueDraftingIdResponse(drafting_id=uuid.uuid4().hex)

    async def save_drafting(self, save_drafting_request: ports.SaveDraftingRequest) -> ports.SaveDraftingResponse:
        drafting_row = save_drafting_request.drafting_row
        path = self._directory / (drafting_row.drafting_id + _SUFFIX)
        written = path.with_name(path.name + "." + uuid.uuid4().hex)
        written.write_text(
            json.dumps(
                {
                    "drafting_id": drafting_row.drafting_id,
                    "job": drafting_row.job,
                    "step": drafting_row.step,
                    "stories": [
                        {"story_id": story_row.story_id, "text": story_row.text} for story_row in drafting_row.stories
                    ],
                    "accepted_stories": [
                        {"story_id": story_row.story_id, "text": story_row.text}
                        for story_row in drafting_row.accepted_stories
                    ],
                }
            )
        )
        os.replace(written, path)
        return ports.SaveDraftingResponse(drafting_id=drafting_row.drafting_id)

    async def load_drafting(self, load_drafting_request: ports.LoadDraftingRequest) -> ports.LoadDraftingResponse:
        path = self._directory / (load_drafting_request.drafting_id + _SUFFIX)
        if path.parent != self._directory or not path.is_file():
            return ports.LoadDraftingResponse(outcome=ports.LoadDraftingOutcome.NOT_FOUND, drafting_rows=())
        row = json.loads(path.read_text())
        return ports.LoadDraftingResponse(
            outcome=ports.LoadDraftingOutcome.FOUND,
            drafting_rows=(
                ports.DraftingRow(
                    drafting_id=row["drafting_id"],
                    job=row["job"],
                    step=row["step"],
                    stories=tuple(
                        ports.StoryRow(story_id=story["story_id"], text=story["text"]) for story in row["stories"]
                    ),
                    accepted_stories=tuple(
                        ports.StoryRow(story_id=story["story_id"], text=story["text"])
                        for story in row["accepted_stories"]
                    ),
                ),
            ),
        )


class FileDraftingStore(ts.Repository):

    def __init__(self, storage: str) -> None:
        self._directory = pathlib.Path(storage)

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.DraftingRepository]:
        self._directory.mkdir(parents=True, exist_ok=True)
        yield FileDraftingRepository(self._directory)
