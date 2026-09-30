# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class JtbdApplicationClient(ts.Client, typing.Protocol):

    async def record_stories(self, record_stories_request: relays.RecordStoriesRequest) -> relays.RecordStoriesResponse: ...
