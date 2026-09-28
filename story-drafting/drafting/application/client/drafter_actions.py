from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.relays as relays


class DrafterApplicationClient(ts.Client, typing.Protocol):

    async def write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse: ...
