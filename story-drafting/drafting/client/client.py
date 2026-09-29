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


class GetJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class StoryView(ts.Response):

    def __init__(self, given: str, when: str, then: str, state: str) -> None:
        self.given = given
        self.when = when
        self.then = then
        self.state = state


class GetJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str, role: str, i_want: str, so_that: str, status: str, stories: tuple[StoryView, ...]) -> None:
        self.jtbd_id = jtbd_id
        self.role = role
        self.i_want = i_want
        self.so_that = so_that
        self.status = status
        self.stories = stories


class DraftingClient(ts.Client, typing.Protocol):

    async def submit_jtbd(self, submit_jtbd_request: SubmitJtbdRequest) -> SubmitJtbdResponse: ...

    async def get_jtbd(self, get_jtbd_request: GetJtbdRequest) -> GetJtbdResponse: ...
