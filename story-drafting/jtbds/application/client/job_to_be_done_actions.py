from __future__ import annotations

import typing

import tesser.application as ts

import jtbds.application.relays as relays


class JobToBeDoneApplicationClient(ts.Client, typing.Protocol):

    async def initialize_jtbd(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> relays.InitializeJtbdResponse: ...
