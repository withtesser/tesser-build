from __future__ import annotations

import contextlib
import typing

import tesser.adapters as ts

import drafting.application.ports as ports


class MemoryRunRepository(ts.Repository):

    def __init__(self, runs: dict[str, ports.Run]) -> None:
        self._runs = runs

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        self._runs[save_run_request.run_id] = ports.Run(
            run_id=save_run_request.run_id,
            job=save_run_request.job,
            stage=save_run_request.stage,
        )
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def load_run(self, load_run_request: ports.LoadRunRequest) -> ports.LoadRunResponse:
        return ports.LoadRunResponse(
            runs=tuple(run for run_id, run in self._runs.items() if run_id == load_run_request.run_id)
        )


class MemoryRunStore(ts.Repository):

    def __init__(self) -> None:
        self._runs: dict[str, ports.Run] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.RunRepository]:
        yield MemoryRunRepository(self._runs)
