from __future__ import annotations

import typing

import tesser.application as ts

import jtbds.application.relays as relays


class JobToBeDoneOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def process_jtbd(self, process_jtbd_request: relays.ProcessJtbdRequest) -> relays.ProcessJtbdResponse: ...

