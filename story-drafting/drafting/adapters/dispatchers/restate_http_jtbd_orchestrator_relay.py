from __future__ import annotations

import typing
import urllib.parse as urllib_parse

import tesser.adapters as ts
import httpx
import restate.client as restate_client

import drafting.adapters.workflows as workflows
import drafting.application.relays as relays

_READ_TIMEOUT_SECONDS: typing.Final[float] = 30.0
_RUN_TIMEOUT: typing.Final[httpx.Timeout] = httpx.Timeout(5.0, read=_READ_TIMEOUT_SECONDS)


class RestateHttpJtbdOrchestratorRelay(ts.Dispatcher):

    def __init__(self, ingress: str, restate_arrange_drafting: workflows.RestateArrangeDrafting) -> None:
        self._ingress = ingress
        self._restate_arrange_drafting = restate_arrange_drafting

    async def run_arrange_drafting(self, arrange_drafting_request: relays.ArrangeDraftingRequest) -> relays.ArrangeDraftingResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_RUN_TIMEOUT) as async_client:
            return await restate_client.Client(async_client).workflow_call(
                self._restate_arrange_drafting.handler,
                key=urllib_parse.quote(arrange_drafting_request.jtbd_id, safe=""),
                arg=arrange_drafting_request,
            )
