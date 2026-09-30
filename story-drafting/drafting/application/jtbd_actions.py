# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.domain as domain


class MapToJtbdSpec(ts.Mapper, domain.JtbdSpec):

    def __init__(self, draft_stories_request: relays.DraftStoriesRequest) -> None:
        super().__init__(
            jtbd_id=draft_stories_request.jtbd_id,
            role=draft_stories_request.role,
            i_want=draft_stories_request.i_want,
            so_that=draft_stories_request.so_that,
            stories=(),
        )


class MapToJtbd(ts.Mapper, ports.Jtbd):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd_id=str(jtbd.jtbd_id),
            role=str(jtbd.role),
            i_want=str(jtbd.i_want),
            so_that=str(jtbd.so_that),
            stories=tuple(ports.Story(given=str(story.given), when=str(story.when), then=str(story.then), state=str(story.state)) for story in jtbd.stories),
        )


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd=MapToJtbd(jtbd),
        )


class MapToDraftStoriesSpec(ts.Mapper, domain.DraftStoriesSpec):

    def __init__(self) -> None:
        super().__init__(
        )


class MapToDraftStoriesResponse(ts.Mapper, relays.DraftStoriesResponse):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd_id=str(jtbd.jtbd_id),
        )


class JtbdActions(ts.Actions):

    def __init__(self, jtbd_store: ports.JtbdStore) -> None:
        self._jtbd_store = jtbd_store

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        jtbd = domain.Jtbd(MapToJtbdSpec(draft_stories_request))
        match jtbd.draft_stories(MapToDraftStoriesSpec()):
            case domain.DraftStoriesOutcome.DRAFTED:
                async with self._jtbd_store.transaction() as jtbd_repository:
                    await jtbd_repository.save_jtbd(MapToSaveJtbdRequest(jtbd))
                return MapToDraftStoriesResponse(jtbd)
            case _ as never:
                typing.assert_never(never)
