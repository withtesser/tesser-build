from __future__ import annotations

import typing

import tesser.application as ts


class Jtbd(ts.Response):

    def __init__(self, jtbd_id: str, job: str, step: str, draft_count: int, picked_draft: str) -> None:
        self.jtbd_id = jtbd_id
        self.job = job
        self.step = step
        self.draft_count = draft_count
        self.picked_draft = picked_draft


class SaveJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, job: str, step: str, draft_count: int, picked_draft: str) -> None:
        self.jtbd_id = jtbd_id
        self.job = job
        self.step = step
        self.draft_count = draft_count
        self.picked_draft = picked_draft


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
