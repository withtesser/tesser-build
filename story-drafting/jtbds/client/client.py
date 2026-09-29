from __future__ import annotations

import typing

import tesser.context as ts


class SubmitJtbdRequest(ts.Request):

    def __init__(self, description: str, status: str) -> None:
        self.description = description
        self.status = status


class SubmitJtbdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class JobToBeDone(ts.Response):

    def __init__(self, jtbd_id: str, description: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.description = description
        self.status = status


class CheckJtbdStatusRequest(ts.Request):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class CheckJtbdStatusResponse(ts.Response):

    def __init__(self, job_to_be_done: JobToBeDone) -> None:
        self.job_to_be_done = job_to_be_done


class JtbdsClient(ts.Client, typing.Protocol):

    async def submit_jtbd(self, submit_jtbd_request: SubmitJtbdRequest) -> SubmitJtbdResponse: ...

    async def check_jtbd_status(self, check_jtbd_status_request: CheckJtbdStatusRequest) -> CheckJtbdStatusResponse: ...
