from __future__ import annotations

import typing

import tesser.application as ts

import jtbd.application.relays as relays


class JtbdApplicationClient(ts.Client, typing.Protocol):

    async def mark_jtbd_drafting(self, mark_jtbd_drafting_request: relays.MarkJtbdDraftingRequest) -> relays.MarkJtbdDraftingResponse: ...
