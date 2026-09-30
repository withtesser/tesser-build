# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import contextlib
import json
import sqlite3
import typing

import tesser.adapters as ts

import drafting.application.ports as ports

_SCHEMA: typing.Final = "CREATE TABLE IF NOT EXISTS jtbds (jtbd_id TEXT PRIMARY KEY, role TEXT NOT NULL, i_want TEXT NOT NULL, so_that TEXT NOT NULL, stories TEXT NOT NULL)"
_UPSERT: typing.Final = "INSERT OR REPLACE INTO jtbds (jtbd_id, role, i_want, so_that, stories) VALUES (?, ?, ?, ?, ?)"
_SELECT: typing.Final = "SELECT role, i_want, so_that, stories FROM jtbds WHERE jtbd_id = ?"


class SqliteJtbdRepositoryTransaction(ts.Repository):

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        jtbd = save_jtbd_request.jtbd
        stories = json.dumps([[story.given, story.when, story.then, story.state] for story in jtbd.stories])
        self._connection.execute(_UPSERT, (jtbd.jtbd_id, jtbd.role, jtbd.i_want, jtbd.so_that, stories))
        return ports.SaveJtbdResponse()

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        row = self._connection.execute(_SELECT, (load_jtbd_request.jtbd_id,)).fetchone()
        if row is None:
            raise KeyError(load_jtbd_request.jtbd_id)
        role, i_want, so_that, stories = row
        return ports.LoadJtbdResponse(
            jtbd=ports.Jtbd(
                jtbd_id=load_jtbd_request.jtbd_id,
                role=str(role),
                i_want=str(i_want),
                so_that=str(so_that),
                stories=tuple(
                    ports.Story(given=str(given), when=str(when), then=str(then), state=str(state))
                    for given, when, then, state in json.loads(str(stories))
                ),
            )
        )


class SqliteJtbdRepository(ts.Repository):

    def __init__(self, location: str) -> None:
        self._location = location

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        connection = sqlite3.connect(self._location, timeout=30)
        try:
            with connection:
                connection.execute(_SCHEMA)
                yield SqliteJtbdRepositoryTransaction(connection)
        finally:
            connection.close()
