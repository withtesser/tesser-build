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
        document = json.dumps(
            {
                "jtbd_id": jtbd.jtbd_id,
                "role": jtbd.role,
                "i_want": jtbd.i_want,
                "so_that": jtbd.so_that,
                "stories": [{"given": story.given, "when": story.when, "then": story.then, "state": story.state} for story in jtbd.stories],
            }
        )
        self._connection.execute("INSERT OR REPLACE INTO jtbds (jtbd_id, document) VALUES (?, ?)", (jtbd.jtbd_id, document))
        return ports.SaveJtbdResponse()

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        row = self._connection.execute("SELECT document FROM jtbds WHERE jtbd_id = ?", (load_jtbd_request.jtbd_id,)).fetchone()
        if row is None:
            raise KeyError(load_jtbd_request.jtbd_id)
        document = json.loads(row[0])
        return ports.LoadJtbdResponse(
            jtbd=ports.Jtbd(
                jtbd_id=document["jtbd_id"],
                role=document["role"],
                i_want=document["i_want"],
                so_that=document["so_that"],
                stories=tuple(ports.Story(given=story["given"], when=story["when"], then=story["then"], state=story["state"]) for story in document["stories"]),
            )
        )


class SqliteJtbdRepository(ts.Repository):

    def __init__(self, location: str) -> None:
        self._location = location
        with contextlib.closing(sqlite3.connect(location)) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS jtbds (jtbd_id TEXT PRIMARY KEY, document TEXT NOT NULL)")
            connection.commit()

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        connection = sqlite3.connect(self._location)
        try:
            yield SqliteJtbdRepositoryTransaction(connection)
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
