from __future__ import annotations

import typing
import urllib.parse as urllib_parse

import tesser.adapters as ts
import httpx
import restate.client as restate_client

import jtbd.adapters.workflows as workflows
import jtbd.application.relays as relays

_READ_TIMEOUT_SECONDS: typing.Final[float] = 30.0
_RUN_TIMEOUT: typing.Final[httpx.Timeout] = httpx.Timeout(5.0, read=_READ_TIMEOUT_SECONDS)


class RestateHttpJtbdOrchestratorRelay(ts.Dispatcher):

    def __init__(self, ingress: str, restate_draft_for_jtbd: workflows.RestateDraftForJtbd) -> None:
        self._ingress = ingress
        self._restate_draft_for_jtbd = restate_draft_for_jtbd

    async def run_draft_for_jtbd(self, draft_for_jtbd_request: relays.DraftForJtbdRequest) -> relays.DraftForJtbdResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_RUN_TIMEOUT) as async_client:
            return await restate_client.Client(async_client).workflow_call(
                self._restate_draft_for_jtbd.handler,
                key=urllib_parse.quote(draft_for_jtbd_request.jtbd_id, safe=""),
                arg=draft_for_jtbd_request,
            )
