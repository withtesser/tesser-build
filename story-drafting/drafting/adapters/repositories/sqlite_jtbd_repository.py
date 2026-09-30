# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import contextlib
import sqlite3
import typing

import tesser.adapters as ts

import drafting.application.ports as ports

_SCHEMA: typing.Final[tuple[str, ...]] = (
    "CREATE TABLE IF NOT EXISTS jtbds ("
    " jtbd_id TEXT PRIMARY KEY,"
    " role TEXT NOT NULL,"
    " i_want TEXT NOT NULL,"
    " so_that TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS stories ("
    " jtbd_id TEXT NOT NULL REFERENCES jtbds (jtbd_id),"
    " position INTEGER NOT NULL,"
    " given_text TEXT NOT NULL,"
    " when_text TEXT NOT NULL,"
    " then_text TEXT NOT NULL,"
    " state TEXT NOT NULL,"
    " PRIMARY KEY (jtbd_id, position))",
)


class SqliteJtbdRepositoryTransaction(ts.Repository):

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        jtbd = save_jtbd_request.jtbd
        self._connection.execute(
            "INSERT INTO jtbds (jtbd_id, role, i_want, so_that) VALUES (?, ?, ?, ?)"
            " ON CONFLICT (jtbd_id) DO UPDATE SET role = excluded.role, i_want = excluded.i_want, so_that = excluded.so_that",
            (jtbd.jtbd_id, jtbd.role, jtbd.i_want, jtbd.so_that),
        )
        self._connection.execute("DELETE FROM stories WHERE jtbd_id = ?", (jtbd.jtbd_id,))
        self._connection.executemany(
            "INSERT INTO stories (jtbd_id, position, given_text, when_text, then_text, state) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (jtbd.jtbd_id, position, story.given, story.when, story.then, story.state)
                for position, story in enumerate(jtbd.stories)
            ],
        )
        return ports.SaveJtbdResponse()

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        jtbd_id = load_jtbd_request.jtbd_id
        found: tuple[str, str, str] | None = self._connection.execute(
            "SELECT role, i_want, so_that FROM jtbds WHERE jtbd_id = ?", (jtbd_id,)
        ).fetchone()
        if found is None:
            raise KeyError(jtbd_id)
        role, i_want, so_that = found
        rows: list[tuple[str, str, str, str]] = self._connection.execute(
            "SELECT given_text, when_text, then_text, state FROM stories WHERE jtbd_id = ? ORDER BY position",
            (jtbd_id,),
        ).fetchall()
        return ports.LoadJtbdResponse(
            jtbd=ports.Jtbd(
                jtbd_id=jtbd_id,
                role=role,
                i_want=i_want,
                so_that=so_that,
                stories=tuple(ports.Story(given=given, when=when, then=then, state=state) for given, when, then, state in rows),
            )
        )


class SqliteJtbdRepository(ts.Repository):

    def __init__(self, location: str) -> None:
        self._location = location

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        with contextlib.closing(sqlite3.connect(self._location, timeout=30)) as connection:
            with connection:
                for statement in _SCHEMA:
                    connection.execute(statement)
                yield SqliteJtbdRepositoryTransaction(connection)
