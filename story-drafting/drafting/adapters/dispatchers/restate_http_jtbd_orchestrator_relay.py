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

    def __init__(self, ingress: str, restate_story_drafting: workflows.RestateStoryDrafting) -> None:
        self._ingress = ingress
        self._restate_story_drafting = restate_story_drafting

    async def start_story_drafting(self, story_drafting_request: relays.StoryDraftingRequest) -> relays.StartStoryDraftingResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_START_TIMEOUT) as async_client:
            await restate_client.Client(async_client).workflow_send(
                self._restate_story_drafting.handler,
                key=urllib_parse.quote(story_drafting_request.jtbd_id, safe=""),
                arg=story_drafting_request,
            )
        return relays.StartStoryDraftingResponse(jtbd_id=story_drafting_request.jtbd_id)
