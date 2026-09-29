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

    def __init__(self, ingress: str, restate_begin_draft_process: workflows.RestateBeginDraftProcess) -> None:
        self._ingress = ingress
        self._restate_begin_draft_process = restate_begin_draft_process

    async def run_begin_draft_process(self, begin_draft_process_request: relays.BeginDraftProcessRequest) -> relays.BeginDraftProcessResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_RUN_TIMEOUT) as async_client:
            return await restate_client.Client(async_client).workflow_call(
                self._restate_begin_draft_process.handler,
                key=urllib_parse.quote(begin_draft_process_request.jtbd_id, safe=""),
                arg=begin_draft_process_request,
            )
