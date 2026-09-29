from __future__ import annotations

import contextlib
import typing

import tesser.adapters as ts

import story_drafting.application.ports as ports


class MemoryJobToBeDoneRepository(ts.Repository):

    def __init__(self, jtbds: dict[str, ports.JobToBeDone]) -> None:
        self._jtbds = jtbds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jtbds[save_jtbd_request.jtbd_id] = ports.JobToBeDone(
            jtbd_id=save_jtbd_request.jtbd_id,
            statement=save_jtbd_request.statement,
            step=save_jtbd_request.step,
            draft_count=save_jtbd_request.draft_count,
            picked_draft=save_jtbd_request.picked_draft,
        )
        return ports.SaveJtbdResponse(jtbd_id=save_jtbd_request.jtbd_id)

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        stored = self._jtbds.get(load_jtbd_request.jtbd_id)
        return ports.LoadJtbdResponse(jtbds=() if stored is None else (stored,))


class MemoryJobToBeDoneStore(ts.Repository):

    def __init__(self) -> None:
        self._jtbds: dict[str, ports.JobToBeDone] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JobToBeDoneRepository]:
        yield MemoryJobToBeDoneRepository(self._jtbds)
