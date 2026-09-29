from __future__ import annotations

import typing

import tesser.context as ts


class SubmitJtbdRequest(ts.Request):

    def __init__(self, situation: str, motivation: str, outcome: str) -> None:
        self.situation = situation
        self.motivation = motivation
        self.outcome = outcome


class SubmitJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class Jtbd(ts.Response):

    def __init__(self, jtbd_id: str, situation: str, motivation: str, outcome: str) -> None:
        self.jtbd_id = jtbd_id
        self.situation = situation
        self.motivation = motivation
        self.outcome = outcome


class CheckStatusRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class CheckStatusResponse(ts.Response):

    def __init__(self, jtbd: Jtbd) -> None:
        self.jtbd = jtbd


class DraftingClient(ts.Client, typing.Protocol):

    async def submit_jtbd(self, submit_jtbd_request: SubmitJtbdRequest) -> SubmitJtbdResponse: ...

    async def check_status(self, check_status_request: CheckStatusRequest) -> CheckStatusResponse: ...
