from __future__ import annotations

import typing

import tesser.application as ts

import jtbd.application.relays as relays


class JtbdOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def draft_for_jtbd(self, draft_for_jtbd_request: relays.DraftForJtbdRequest) -> relays.DraftForJtbdResponse: ...

