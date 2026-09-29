from __future__ import annotations

import typing
import urllib.parse as urllib_parse

import tesser.adapters as ts
import httpx
import restate.client as restate_client

import drafting.adapters.workflows as workflows
import drafting.application.relays as relays

_READ_TIMEOUT_SECONDS: typing.Final[float] = 30.0
_SEND_TIMEOUT: typing.Final[httpx.Timeout] = httpx.Timeout(5.0, read=_READ_TIMEOUT_SECONDS)


class RestateHttpJtbdOrchestratorRelay(ts.Dispatcher):

    def __init__(self, ingress: str, restate_draft_jtbd: workflows.RestateDraftJtbd) -> None:
        self._ingress = ingress
        self._restate_draft_jtbd = restate_draft_jtbd

    async def start_draft_jtbd(self, draft_jtbd_request: relays.DraftJtbdRequest) -> relays.StartDraftJtbdResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_SEND_TIMEOUT) as async_client:
            await restate_client.Client(async_client).workflow_send(
                self._restate_draft_jtbd.handler,
                key=urllib_parse.quote(draft_jtbd_request.jtbd_id, safe=""),
                arg=draft_jtbd_request,
            )
        return relays.StartDraftJtbdResponse(jtbd_id=draft_jtbd_request.jtbd_id)
