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


class RestateHttpJtbdOrchestratorRelay(ts.Dispatcher):

    def __init__(self, ingress: str, restate_conduct_drafting: workflows.RestateConductDrafting) -> None:
        self._ingress = ingress
        self._restate_conduct_drafting = restate_conduct_drafting

    async def run_conduct_drafting(self, conduct_drafting_request: relays.ConductDraftingRequest) -> relays.ConductDraftingResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_RUN_TIMEOUT) as async_client:
            return await restate_client.Client(async_client).workflow_call(
                self._restate_conduct_drafting.handler,
                key=urllib_parse.quote(conduct_drafting_request.jtbd_id, safe=""),
                arg=conduct_drafting_request,
            )
