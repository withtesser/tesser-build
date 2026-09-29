from __future__ import annotations

import typing

import tesser.application as ts

import story_drafting.application.relays as relays


class JtbdApplicationClient(ts.Client, typing.Protocol):

    async def initialize_jtbd(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> relays.InitializeJtbdResponse: ...
