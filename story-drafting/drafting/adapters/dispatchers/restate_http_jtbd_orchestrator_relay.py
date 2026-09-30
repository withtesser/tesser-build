# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import typing
import urllib.parse as urllib_parse

import tesser.adapters as ts
import httpx
import restate.client as restate_client

import drafting.adapters.workflows as workflows
import drafting.application.relays as relays

_READ_TIMEOUT_SECONDS: typing.Final[float] = 30.0
_START_TIMEOUT: typing.Final[httpx.Timeout] = httpx.Timeout(5.0, read=_READ_TIMEOUT_SECONDS)


class RestateHttpJtbdOrchestratorRelay(ts.Dispatcher):

    def __init__(self, ingress: str, restate_conduct_story_drafting: workflows.RestateConductStoryDrafting) -> None:
        self._ingress = ingress
        self._restate_conduct_story_drafting = restate_conduct_story_drafting

    async def start_conduct_story_drafting(self, conduct_story_drafting_request: relays.ConductStoryDraftingRequest) -> relays.StartConductStoryDraftingResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_START_TIMEOUT) as async_client:
            await restate_client.Client(async_client).workflow_send(
                self._restate_conduct_story_drafting.handler,
                key=urllib_parse.quote(conduct_story_drafting_request.jtbd_id, safe=""),
                arg=conduct_story_drafting_request,
            )
        return relays.StartConductStoryDraftingResponse(jtbd_id=conduct_story_drafting_request.jtbd_id)
