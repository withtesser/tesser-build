from __future__ import annotations

import typing

import tesser.context as ts


class SubmitJtbdRequest(ts.Request):

    def __init__(self, job: str) -> None:
        self.job = job


class SubmitJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class Jtbd(ts.Response):

    def __init__(self, jtbd_id: str, job: str) -> None:
        self.jtbd_id = jtbd_id
        self.job = job


class GetJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class GetJtbdResponse(ts.Response):

    def __init__(self, jtbd: Jtbd) -> None:
        self.jtbd = jtbd


class StoryDraftingClient(ts.Client, typing.Protocol):

    async def submit_jtbd(self, submit_jtbd_request: SubmitJtbdRequest) -> SubmitJtbdResponse: ...

    async def get_jtbd(self, get_jtbd_request: GetJtbdRequest) -> GetJtbdResponse: ...
