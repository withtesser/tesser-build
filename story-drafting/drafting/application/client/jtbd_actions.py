from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class JtbdApplicationClient(ts.Client, typing.Protocol):

    async def write_drafts(self, write_drafts_request: relays.WriteDraftsRequest) -> relays.WriteDraftsResponse: ...
