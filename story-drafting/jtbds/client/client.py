from __future__ import annotations

import typing

import tesser.context as ts


class SubmitJtbdRequest(ts.Request):

    def __init__(self, job: str, step: str, draft_count: int, picked_draft: str) -> None:
        self.job = job
        self.step = step
        self.draft_count = draft_count
        self.picked_draft = picked_draft


class SubmitJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class Jtbd(ts.Response):

    def __init__(self, jtbd_id: str, job: str, step: str, draft_count: int, picked_draft: str) -> None:
        self.jtbd_id = jtbd_id
        self.job = job
        self.step = step
        self.draft_count = draft_count
        self.picked_draft = picked_draft


class GetJtbdRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class GetJtbdResponse(ts.Response):

    def __init__(self, jtbd: Jtbd) -> None:
        self.jtbd = jtbd


class JtbdsClient(ts.Client, typing.Protocol):

    async def submit_jtbd(self, submit_jtbd_request: SubmitJtbdRequest) -> SubmitJtbdResponse: ...

    async def get_jtbd(self, get_jtbd_request: GetJtbdRequest) -> GetJtbdResponse: ...
