from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class RunOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def conduct_run(self, conduct_run_request: relays.ConductRunRequest) -> relays.ConductRunResponse: ...
