from __future__ import annotations

import typing

import tesser.application as ts

import story_drafting.application.relays as relays


class JobToBeDoneOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def work_through_jtbd(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest) -> relays.WorkThroughJtbdResponse: ...

