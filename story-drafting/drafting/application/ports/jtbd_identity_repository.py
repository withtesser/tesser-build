from __future__ import annotations

import typing

import tesser.application as ts


class IssueJtbdIdRequest(ts.Request):

    def __init__(self) -> None:
        return None


class IssueJtbdIdResponse(ts.Response):

    def __init__(self, jtbd_id: str) -> None:
        self.jtbd_id = jtbd_id


class JtbdIdentityRepository(ts.Port, typing.Protocol):

    async def issue_jtbd_id(self, issue_jtbd_id_request: IssueJtbdIdRequest) -> IssueJtbdIdResponse: ...
