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


class ComeBackToJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class ComeBackToJtbdResponse(ts.Response):

    def __init__(self, jtbd: Jtbd) -> None:
        self.jtbd = jtbd


class StoryDraftingClient(ts.Client, typing.Protocol):

    async def submit_jtbd(self, submit_jtbd_request: SubmitJtbdRequest) -> SubmitJtbdResponse: ...

    async def come_back_to_jtbd(self, come_back_to_jtbd_request: ComeBackToJtbdRequest) -> ComeBackToJtbdResponse: ...
