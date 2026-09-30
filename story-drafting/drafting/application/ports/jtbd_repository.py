# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import typing

import tesser.application as ts


class StoryView(ts.Response):

    def __init__(self, given: str, when: str, then: str, state: str) -> None:
        self.given = given
        self.when = when
        self.then = then
        self.state = state


class Jtbd(ts.Response):

    def __init__(self, jtbd_id: str, role: str, i_want: str, so_that: str, stories: tuple[StoryView, ...]) -> None:
        self.jtbd_id = jtbd_id
        self.role = role
        self.i_want = i_want
        self.so_that = so_that
        self.stories = stories


class SaveJtbdRequest(ts.Request):

    def __init__(self, jtbd: Jtbd) -> None:
        self.jtbd = jtbd


class SaveJtbdResponse(ts.Response):

    def __init__(self) -> None:
        return None


class LoadJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class LoadJtbdResponse(ts.Response):

    def __init__(self, jtbd: Jtbd) -> None:
        self.jtbd = jtbd


class JtbdRepository(ts.Port, typing.Protocol):

    async def save_jtbd(self, save_jtbd_request: SaveJtbdRequest) -> SaveJtbdResponse: ...

    async def load_jtbd(self, load_jtbd_request: LoadJtbdRequest) -> LoadJtbdResponse: ...


class JtbdStore(ts.Store, typing.Protocol):

    def transaction(self) -> typing.AsyncContextManager[JtbdRepository]: ...
