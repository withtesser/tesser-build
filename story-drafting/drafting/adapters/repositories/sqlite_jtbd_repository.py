# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import contextlib
import sqlite3
import typing

import tesser.adapters as ts

import drafting.application.ports as ports

_SCHEMA: typing.Final = (
    "CREATE TABLE IF NOT EXISTS jtbds (jtbd_id TEXT PRIMARY KEY, role TEXT NOT NULL, i_want TEXT NOT NULL, so_that TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS stories (jtbd_id TEXT NOT NULL, position INTEGER NOT NULL, given TEXT NOT NULL, story_when TEXT NOT NULL, story_then TEXT NOT NULL, state TEXT NOT NULL, PRIMARY KEY (jtbd_id, position))",
)


class SqliteJtbdRepositoryTransaction(ts.Repository):

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        jtbd = save_jtbd_request.jtbd
        self._connection.execute(
            "INSERT OR REPLACE INTO jtbds (jtbd_id, role, i_want, so_that) VALUES (?, ?, ?, ?)",
            (jtbd.jtbd_id, jtbd.role, jtbd.i_want, jtbd.so_that),
        )
        self._connection.execute("DELETE FROM stories WHERE jtbd_id = ?", (jtbd.jtbd_id,))
        self._connection.executemany(
            "INSERT INTO stories (jtbd_id, position, given, story_when, story_then, state) VALUES (?, ?, ?, ?, ?, ?)",
            [(jtbd.jtbd_id, position, story.given, story.when, story.then, story.state) for position, story in enumerate(jtbd.stories)],
        )
        return ports.SaveJtbdResponse()

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        row = self._connection.execute(
            "SELECT jtbd_id, role, i_want, so_that FROM jtbds WHERE jtbd_id = ?", (load_jtbd_request.jtbd_id,)
        ).fetchone()
        if row is None:
            raise KeyError(load_jtbd_request.jtbd_id)
        story_rows = self._connection.execute(
            "SELECT given, story_when, story_then, state FROM stories WHERE jtbd_id = ? ORDER BY position", (load_jtbd_request.jtbd_id,)
        ).fetchall()
        return ports.LoadJtbdResponse(
            jtbd=ports.Jtbd(
                jtbd_id=row[0],
                role=row[1],
                i_want=row[2],
                so_that=row[3],
                stories=tuple(ports.Story(given=given, when=when, then=then, state=state) for given, when, then, state in story_rows),
            )
        )


class SqliteJtbdRepository(ts.Repository):

    def __init__(self, location: str) -> None:
        self._location = location

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        connection = sqlite3.connect(self._location)
        try:
            for statement in _SCHEMA:
                connection.execute(statement)
            yield SqliteJtbdRepositoryTransaction(connection)
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
