from __future__ import annotations

import typing

import tesser.application as ts


class Jtbd(ts.Response):

    def __init__(self, jtbd_id: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.status = status


class SaveJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.status = status


class SaveJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class LoadJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class LoadJtbdResponse(ts.Response):

    def __init__(self, jtbds: tuple[Jtbd, ...]) -> None:
        self.jtbds = jtbds


class JtbdRepository(ts.Port, typing.Protocol):

    async def save_jtbd(self, save_jtbd_request: SaveJtbdRequest) -> SaveJtbdResponse: ...

    async def load_jtbd(self, load_jtbd_request: LoadJtbdRequest) -> LoadJtbdResponse: ...


class JtbdStore(ts.Store, typing.Protocol):

    def transaction(self) -> typing.AsyncContextManager[JtbdRepository]: ...
