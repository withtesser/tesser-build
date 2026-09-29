from __future__ import annotations

import typing

import tesser.application as ts


class JobToBeDone(ts.Response):

    def __init__(self, jtbd_id: str, statement: str, step: str, draft_count: int, picked_draft: str) -> None:
        self.jtbd_id = jtbd_id
        self.statement = statement
        self.step = step
        self.draft_count = draft_count
        self.picked_draft = picked_draft


class SaveJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str, statement: str, step: str, draft_count: int, picked_draft: str) -> None:
        self.jtbd_id = jtbd_id
        self.statement = statement
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

    def __init__(self, jtbds: tuple[JobToBeDone, ...]) -> None:
        self.jtbds = jtbds


class JobToBeDoneRepository(ts.Port, typing.Protocol):

    async def save_jtbd(self, save_jtbd_request: SaveJtbdRequest) -> SaveJtbdResponse: ...

    async def load_jtbd(self, load_jtbd_request: LoadJtbdRequest) -> LoadJtbdResponse: ...


class JobToBeDoneStore(ts.Store, typing.Protocol):

    def transaction(self) -> typing.AsyncContextManager[JobToBeDoneRepository]: ...
