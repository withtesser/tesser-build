from __future__ import annotations

import typing

import tesser.application as ts

import story_drafting.application.relays as relays


class JobToBeDoneApplicationClient(ts.Client, typing.Protocol):

    async def record_jtbd(self, record_jtbd_request: relays.RecordJtbdRequest) -> relays.RecordJtbdResponse: ...
