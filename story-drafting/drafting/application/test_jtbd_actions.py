# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays


@ts.fake
class FakeJtbdRepository(ports.JtbdRepository):

    def __init__(self, jtbds: dict[str, ports.Jtbd]) -> None:
        self._jtbds = jtbds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jtbds[save_jtbd_request.jtbd.jtbd_id] = save_jtbd_request.jtbd
        return ports.SaveJtbdResponse()

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        return ports.LoadJtbdResponse(jtbd=self._jtbds[load_jtbd_request.jtbd_id])


@ts.fake
class FakeJtbdStore(ports.JtbdStore):

    def __init__(self) -> None:
        self.jtbds: dict[str, ports.Jtbd] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        yield FakeJtbdRepository(self.jtbds)


class TestJtbdActions:

    async def test_record_stories_answers_for_the_jtbd_it_builds(self) -> None:
        fake_jtbd_store = FakeJtbdStore()

        record_stories_response = await application.JtbdActions(fake_jtbd_store).record_stories(
            relays.RecordStoriesRequest(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away and return", story_texts=(relays.JtbdActionsStoryText(given="a job to be done", when="I submit it", then="it is drafting"),))
        )

        assert record_stories_response.jtbd_id == "jtbd-1"
