from __future__ import annotations

import typing
import urllib.parse as urllib_parse

import tesser.adapters as ts
import httpx
import restate.client as restate_client

import story_drafting.adapters.workflows as workflows
import story_drafting.application.relays as relays

_READ_TIMEOUT_SECONDS: typing.Final[float] = 30.0
_RUN_TIMEOUT: typing.Final[httpx.Timeout] = httpx.Timeout(5.0, read=_READ_TIMEOUT_SECONDS)


class RestateHttpJobToBeDoneOrchestratorRelay(ts.Dispatcher):

    def __init__(self, ingress: str, restate_work_through_jtbd: workflows.RestateWorkThroughJtbd) -> None:
        self._ingress = ingress
        self._restate_work_through_jtbd = restate_work_through_jtbd

    async def run_work_through_jtbd(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest) -> relays.WorkThroughJtbdResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_RUN_TIMEOUT) as async_client:
            return await restate_client.Client(async_client).workflow_call(
                self._restate_work_through_jtbd.handler,
                key=urllib_parse.quote(work_through_jtbd_request.jtbd_id, safe=""),
                arg=work_through_jtbd_request,
            )
