# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import contextlib
import json
import sqlite3
import typing

import tesser.adapters as ts

import drafting.application.ports as ports


class SqliteJtbdRepositoryTransaction(ts.Repository):

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        jtbd = save_jtbd_request.jtbd
        stories = [{"given": story.given, "when": story.when, "then": story.then, "state": story.state} for story in jtbd.stories]
        self._connection.execute(
            "INSERT OR REPLACE INTO jtbds (jtbd_id, role, i_want, so_that, stories) VALUES (?, ?, ?, ?, ?)",
            (jtbd.jtbd_id, jtbd.role, jtbd.i_want, jtbd.so_that, json.dumps(stories)),
        )
        return ports.SaveJtbdResponse()

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        row = self._connection.execute(
            "SELECT jtbd_id, role, i_want, so_that, stories FROM jtbds WHERE jtbd_id = ?", (load_jtbd_request.jtbd_id,)
        ).fetchone()
        if row is None:
            raise KeyError(load_jtbd_request.jtbd_id)
        stories = tuple(
            ports.StoryView(given=story["given"], when=story["when"], then=story["then"], state=story["state"])
            for story in json.loads(row[4])
        )
        return ports.LoadJtbdResponse(jtbd=ports.Jtbd(jtbd_id=row[0], role=row[1], i_want=row[2], so_that=row[3], stories=stories))


class SqliteJtbdRepository(ts.Repository):

    def __init__(self, location: str) -> None:
        self._location = location
        connection = sqlite3.connect(location)
        try:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS jtbds (jtbd_id TEXT PRIMARY KEY, role TEXT NOT NULL, i_want TEXT NOT NULL, so_that TEXT NOT NULL, stories TEXT NOT NULL)"
            )
            connection.commit()
        finally:
            connection.close()

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        connection = sqlite3.connect(self._location, timeout=30)
        try:
            yield SqliteJtbdRepositoryTransaction(connection)
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
