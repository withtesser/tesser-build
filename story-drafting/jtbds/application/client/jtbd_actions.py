from __future__ import annotations

import typing

import tesser.application as ts

import jtbds.application.relays as relays


class JtbdApplicationClient(ts.Client, typing.Protocol):

    async def record_jtbd(self, record_jtbd_request: relays.RecordJtbdRequest) -> relays.RecordJtbdResponse: ...
