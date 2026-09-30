# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import typing

import tesser.context as ts


class SubmitJtbdRequest(ts.Request):

    def __init__(self, role: str, i_want: str, so_that: str) -> None:
        self.role = role
        self.i_want = i_want
        self.so_that = so_that


class SubmitJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.status = status


class ReadJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class Story(ts.Response):

    def __init__(self, given: str, when: str, then: str, state: str) -> None:
        self.given = given
        self.when = when
        self.then = then
        self.state = state


class ReadJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str, status: str, stories: tuple[Story, ...]) -> None:
        self.jtbd_id = jtbd_id
        self.status = status
        self.stories = stories


class DraftingClient(ts.Client, typing.Protocol):

    async def submit_jtbd(self, submit_jtbd_request: SubmitJtbdRequest) -> SubmitJtbdResponse: ...

    async def read_jtbd(self, read_jtbd_request: ReadJtbdRequest) -> ReadJtbdResponse: ...
