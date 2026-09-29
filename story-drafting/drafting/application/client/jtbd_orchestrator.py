from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class JtbdOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def draft_jtbd(self, draft_jtbd_request: relays.DraftJtbdRequest) -> relays.DraftJtbdResponse: ...

