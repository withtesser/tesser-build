from __future__ import annotations

import typing

import tesser.application as ts


class IssueRunIdRequest(ts.Request):

    def __init__(self) -> None:
        return None


class IssueRunIdResponse(ts.Response):

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class RunIdentityRepository(ts.Port, typing.Protocol):

    async def issue_run_id(self, issue_run_id_request: IssueRunIdRequest) -> IssueRunIdResponse: ...
