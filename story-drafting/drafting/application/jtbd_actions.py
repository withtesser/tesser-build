# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.domain as domain


class MapToJtbdSpec(ts.Mapper, domain.JtbdSpec):

    def __init__(self, record_drafted_stories_request: relays.RecordDraftedStoriesRequest) -> None:
        super().__init__(
            jtbd_id=record_drafted_stories_request.jtbd_id,
            role=record_drafted_stories_request.role,
            i_want=record_drafted_stories_request.i_want,
            so_that=record_drafted_stories_request.so_that,
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


class MapToRecordStoriesSpec(ts.Mapper, domain.RecordStoriesSpec):

    def __init__(self, record_drafted_stories_request: relays.RecordDraftedStoriesRequest) -> None:
        super().__init__(
            story_texts=tuple(domain.StoryTextSpec(given=story_text.given, when=story_text.when, then=story_text.then) for story_text in record_drafted_stories_request.story_texts),
        )


class MapToRecordDraftedStoriesResponse(ts.Mapper, relays.RecordDraftedStoriesResponse):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd_id=str(jtbd.jtbd_id),
        )


class JtbdActions(ts.Actions):

    def __init__(self, jtbd_store: ports.JtbdStore) -> None:
        self._jtbd_store = jtbd_store

    async def record_drafted_stories(self, record_drafted_stories_request: relays.RecordDraftedStoriesRequest) -> relays.RecordDraftedStoriesResponse:
        jtbd = domain.Jtbd(MapToJtbdSpec(record_drafted_stories_request))
        match jtbd.record_stories(MapToRecordStoriesSpec(record_drafted_stories_request)):
            case domain.RecordStoriesOutcome.RECORDED:
                async with self._jtbd_store.transaction() as jtbd_repository:
                    await jtbd_repository.save_jtbd(MapToSaveJtbdRequest(jtbd))
                return MapToRecordDraftedStoriesResponse(jtbd)
            case _ as never:
                typing.assert_never(never)
