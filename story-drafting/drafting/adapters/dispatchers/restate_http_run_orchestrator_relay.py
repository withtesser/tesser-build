from __future__ import annotations

import typing
import urllib.parse as urllib_parse

import tesser.adapters as ts
import httpx
import restate.client as restate_client

import drafting.adapters.workflows as workflows
import drafting.application.relays as relays

_TIMEOUT: typing.Final[httpx.Timeout] = httpx.Timeout(5.0, read=30.0)


class RestateHttpRunOrchestratorRelay(ts.Dispatcher):

    def __init__(self, ingress: str, restate_conduct_run: workflows.RestateConductRun) -> None:
        self._ingress = ingress
        self._restate_conduct_run = restate_conduct_run

    async def start_conduct_run(self, conduct_run_request: relays.ConductRunRequest) -> relays.StartConductRunResponse:
        async with httpx.AsyncClient(base_url=self._ingress, timeout=_TIMEOUT) as async_client:
            await restate_client.Client(async_client).workflow_send(
                self._restate_conduct_run.handler,
                key=urllib_parse.quote(conduct_run_request.run_id, safe="").replace(".", "%2E"),
                arg=conduct_run_request,
            )
        return relays.StartConductRunResponse(run_id=conduct_run_request.run_id)
