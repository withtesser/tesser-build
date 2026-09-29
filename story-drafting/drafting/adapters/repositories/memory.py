from __future__ import annotations

import contextlib
import typing

import tesser.adapters as ts

import drafting.application.ports as ports


class MemoryRunRepository(ts.Repository):

    def __init__(self, run_records: dict[str, ports.RunRecord]) -> None:
        self._run_records = run_records

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        self._run_records[save_run_request.run_id] = ports.RunRecord(
            run_id=save_run_request.run_id,
            job=save_run_request.job,
            stage=save_run_request.stage,
            stories=save_run_request.stories,
            accepted_stories=save_run_request.accepted_stories,
        )
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def load_run(self, load_run_request: ports.LoadRunRequest) -> ports.LoadRunResponse:
        run_record = self._run_records.get(load_run_request.run_id)
        if run_record is None:
            return ports.LoadRunResponse(outcome=ports.LoadRunOutcome.NOT_FOUND, runs=())
        return ports.LoadRunResponse(outcome=ports.LoadRunOutcome.FOUND, runs=(run_record,))


class MemoryRunStore(ts.Repository):

    def __init__(self) -> None:
        self._run_records: dict[str, ports.RunRecord] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.RunRepository]:
        yield MemoryRunRepository(self._run_records)
