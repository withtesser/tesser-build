from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class RunApplicationClient(ts.Client, typing.Protocol):

    async def keep_run(self, keep_run_request: relays.KeepRunRequest) -> relays.KeepRunResponse: ...
