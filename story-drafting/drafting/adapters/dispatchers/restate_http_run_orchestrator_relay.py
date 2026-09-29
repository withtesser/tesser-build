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


class RestateHttpRunOrchestratorRelay(ts.Dispatcher):

    def __init__(self, ingress: str, restate_conduct_run: workflows.RestateConductRun) -> None:
        self._ingress = ingress
        self._restate_conduct_run = restate_conduct_run

    async def run_conduct_run(self, conduct_run_request: relays.ConductRunRequest) -> relays.ConductRunResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_RUN_TIMEOUT) as async_client:
            return await restate_client.Client(async_client).workflow_call(
                self._restate_conduct_run.handler,
                key=urllib_parse.quote(conduct_run_request.run_id, safe=""),
                arg=conduct_run_request,
            )
