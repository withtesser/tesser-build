from __future__ import annotations

import contextlib
import typing

import tesser.adapters as ts

import jtbd.application.ports as ports


class MemoryJtbdRepository(ts.Repository):

    def __init__(self, jbtds: dict[str, ports.Jtbd]) -> None:
        self._jbtds = jbtds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jbtds[save_jtbd_request.jtbd_id] = ports.Jtbd(
            jtbd_id=save_jtbd_request.jtbd_id,
            description=save_jtbd_request.description,
            status=save_jtbd_request.status,
        )
        return ports.SaveJtbdResponse(jtbd_id=save_jtbd_request.jtbd_id)

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        stored = self._jbtds.get(load_jtbd_request.jtbd_id)
        return ports.LoadJtbdResponse(jbtds=() if stored is None else (stored,))


class MemoryJtbdStore(ts.Repository):

    def __init__(self) -> None:
        self._jbtds: dict[str, ports.Jtbd] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        yield MemoryJtbdRepository(self._jbtds)
