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
        self._jtbds[save_jtbd_request.jtbd_id] = ports.Jtbd(
            jtbd_id=save_jtbd_request.jtbd_id,
            situation=save_jtbd_request.situation,
            motivation=save_jtbd_request.motivation,
            outcome=save_jtbd_request.outcome,
        )
        return ports.SaveJtbdResponse(jtbd_id=save_jtbd_request.jtbd_id)

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        return ports.LoadJtbdResponse(jtbds=(self._jtbds[load_jtbd_request.jtbd_id],))


@ts.fake
class FakeJtbdStore(ports.JtbdStore):

    def __init__(self) -> None:
        self.jtbds: dict[str, ports.Jtbd] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        yield FakeJtbdRepository(self.jtbds)


class TestJtbdActions:

    async def test_record_jtbd_saves_the_jtbd_under_its_jtbd_id(self) -> None:
        fake_jtbd_store = FakeJtbdStore()
        jtbd_actions = application.JtbdActions(fake_jtbd_store)

        await jtbd_actions.record_jtbd(
            relays.RecordJtbdRequest(jtbd_id="jtbd-1", situation="I am working through a multi-step piece of work with an agent", motivation="the steps and my checkpoints fixed in advance", outcome="I can step away and resume where we were")
        )

        assert fake_jtbd_store.jtbds["jtbd-1"] == ports.Jtbd(
            jtbd_id="jtbd-1", situation="I am working through a multi-step piece of work with an agent", motivation="the steps and my checkpoints fixed in advance", outcome="I can step away and resume where we were"
        )

    async def test_record_jtbd_answers_the_jtbd_id_it_saved(self) -> None:
        jtbd_actions = application.JtbdActions(FakeJtbdStore())

        record_jtbd_response = await jtbd_actions.record_jtbd(
            relays.RecordJtbdRequest(jtbd_id="jtbd-1", situation="I am working through a multi-step piece of work with an agent", motivation="the steps and my checkpoints fixed in advance", outcome="I can step away and resume where we were")
        )

        assert record_jtbd_response.jtbd_id == "jtbd-1"
