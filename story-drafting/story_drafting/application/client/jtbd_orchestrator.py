from __future__ import annotations

import typing

import tesser.application as ts

import story_drafting.application.relays as relays


class JtbdOrchestratorApplicationClient(ts.Client, typing.Protocol):

    async def begin_draft_process(self, begin_draft_process_request: relays.BeginDraftProcessRequest) -> relays.BeginDraftProcessResponse: ...

