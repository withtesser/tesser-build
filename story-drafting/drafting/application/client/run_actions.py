from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class RunApplicationClient(ts.Client, typing.Protocol):

    async def record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse: ...
