from __future__ import annotations

import contextlib
import typing

import tesser.adapters as ts

import story_drafting.application.ports as ports


class MemoryJtbdRepository(ts.Repository):

    def __init__(self, jtbds: dict[str, ports.Jtbd]) -> None:
        self._jtbds = jtbds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jtbds[save_jtbd_request.jtbd_id] = ports.Jtbd(
            jtbd_id=save_jtbd_request.jtbd_id,
            status=save_jtbd_request.status,
        )
        return ports.SaveJtbdResponse(jtbd_id=save_jtbd_request.jtbd_id)

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        stored = self._jtbds.get(load_jtbd_request.jtbd_id)
        return ports.LoadJtbdResponse(jtbds=() if stored is None else (stored,))


class MemoryJtbdStore(ts.Repository):

    def __init__(self) -> None:
        self._jtbds: dict[str, ports.Jtbd] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        yield MemoryJtbdRepository(self._jtbds)
