from __future__ import annotations

import typing

import tesser.application as ts


class JobToBeDone(ts.Response):

    def __init__(self, jtbd_id: str, description: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.description = description
        self.status = status


class SaveJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, description: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.description = description
        self.status = status


class SaveJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class LoadJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class LoadJtbdResponse(ts.Response):

    def __init__(self, jtbds: tuple[JobToBeDone, ...]) -> None:
        self.jtbds = jtbds


class JobToBeDoneRepository(ts.Port, typing.Protocol):

    async def save_jtbd(self, save_jtbd_request: SaveJtbdRequest) -> SaveJtbdResponse: ...

    async def load_jtbd(self, load_jtbd_request: LoadJtbdRequest) -> LoadJtbdResponse: ...


class JobToBeDoneStore(ts.Store, typing.Protocol):

    def transaction(self) -> typing.AsyncContextManager[JobToBeDoneRepository]: ...
