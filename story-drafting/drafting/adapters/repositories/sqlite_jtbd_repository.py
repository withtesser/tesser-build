# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import contextlib
import typing

import tesser.adapters as ts

import drafting.application.ports as ports


class SqliteJtbdRepositoryTransaction(ts.Repository):

    def __init__(self, jtbds: dict[str, ports.Jtbd]) -> None:
        self._jtbds = jtbds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jtbds[save_jtbd_request.jtbd.jtbd_id] = save_jtbd_request.jtbd
        return ports.SaveJtbdResponse()

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        return ports.LoadJtbdResponse(jtbd=self._jtbds[load_jtbd_request.jtbd_id])


class SqliteJtbdRepository(ts.Repository):

    def __init__(self, location: str) -> None:
        self._jtbds: dict[str, ports.Jtbd] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        yield SqliteJtbdRepositoryTransaction(self._jtbds)
