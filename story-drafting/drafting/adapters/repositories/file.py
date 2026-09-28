from __future__ import annotations

import contextlib
import json
import os
import pathlib
import typing
import uuid

import tesser.adapters as ts

import drafting.application.ports as ports


class FileRunRepository(ts.Repository):

    def __init__(self, directory: pathlib.Path) -> None:
        self._directory = directory

    async def issue_run_id(self, issue_run_id_request: ports.IssueRunIdRequest) -> ports.IssueRunIdResponse:
        return ports.IssueRunIdResponse(run_id=str(uuid.uuid4()))

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        row = {
            "run_id": save_run_request.run_id,
            "job": save_run_request.job,
            "step": save_run_request.step,
            "drafted_stories": list(save_run_request.drafted_stories),
            "accepted_stories": list(save_run_request.accepted_stories),
        }
        written = self._directory / f"{save_run_request.run_id}.json.tmp"
        written.write_text(json.dumps(row))
        os.replace(written, self._directory / f"{save_run_request.run_id}.json")
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def load_run(self, load_run_request: ports.LoadRunRequest) -> ports.LoadRunResponse:
        kept = self._directory / f"{load_run_request.run_id}.json"
        if not kept.is_file():
            return ports.LoadRunResponse(outcome=ports.LoadRunOutcome.NOT_FOUND, runs=())
        row = json.loads(kept.read_text())
        return ports.LoadRunResponse(
            outcome=ports.LoadRunOutcome.FOUND,
            runs=(
                ports.Run(
                    run_id=row["run_id"],
                    job=row["job"],
                    step=row["step"],
                    drafted_stories=tuple(row["drafted_stories"]),
                    accepted_stories=tuple(row["accepted_stories"]),
                ),
            ),
        )


class FileRunStore(ts.Repository):

    def __init__(self, storage: str) -> None:
        self._storage = storage

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.RunRepository]:
        directory = pathlib.Path(self._storage)
        directory.mkdir(parents=True, exist_ok=True)
        yield FileRunRepository(directory)
