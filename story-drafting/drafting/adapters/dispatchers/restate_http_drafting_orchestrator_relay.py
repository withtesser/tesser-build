from __future__ import annotations

import typing
import urllib.parse as urllib_parse

import tesser.adapters as ts
import httpx
import restate.client as restate_client

import drafting.adapters.workflows as workflows
import drafting.application.relays as relays

_TIMEOUT: typing.Final[httpx.Timeout] = httpx.Timeout(5.0, read=30.0)


class RestateHttpDraftingOrchestratorRelay(ts.Dispatcher):

    def __init__(self, ingress: str, restate_conduct_drafting: workflows.RestateConductDrafting) -> None:
        self._ingress = ingress
        self._restate_conduct_drafting = restate_conduct_drafting

    async def start_conduct_drafting(
        self, conduct_drafting_request: relays.ConductDraftingRequest
    ) -> relays.StartConductDraftingResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_TIMEOUT) as async_client:
            await restate_client.Client(async_client).workflow_send(
                self._restate_conduct_drafting.handler,
                key=urllib_parse.quote(conduct_drafting_request.drafting_id, safe="").replace(".", "%2E"),
                arg=conduct_drafting_request,
            )
        return relays.StartConductDraftingResponse(drafting_id=conduct_drafting_request.drafting_id)
