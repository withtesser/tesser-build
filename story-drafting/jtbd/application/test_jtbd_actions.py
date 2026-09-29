from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import jtbd.application as application
import jtbd.application.ports as ports
import jtbd.application.relays as relays


@ts.fake
class FakeJtbdRepository(ports.JtbdRepository):

    def __init__(self, jbtds: dict[str, ports.Jtbd]) -> None:
        self._jbtds = jbtds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jbtds[save_jtbd_request.jtbd_id] = ports.Jtbd(
            jtbd_id=save_jtbd_request.jtbd_id,
            description=save_jtbd_request.description,
            status=save_jtbd_request.status,
        )
        return ports.SaveJtbdResponse(jtbd_id=save_jtbd_request.jtbd_id)

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        return ports.LoadJtbdResponse(jbtds=(self._jbtds[load_jtbd_request.jtbd_id],))


@ts.fake
class FakeJtbdStore(ports.JtbdStore):

    def __init__(self) -> None:
        self.jbtds: dict[str, ports.Jtbd] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JtbdRepository]:
        yield FakeJtbdRepository(self.jbtds)


class TestJtbdActions:

    async def test_mark_jtbd_drafting_saves_the_jtbd_under_its_jtbd_id(self) -> None:
        fake_jtbd_store = FakeJtbdStore()
        jtbd_actions = application.JtbdActions(fake_jtbd_store)

        await jtbd_actions.mark_jtbd_drafting(
            relays.MarkJtbdDraftingRequest(jtbd_id="jtbd-1", description="design-feature", status="drafting")
        )

        assert fake_jtbd_store.jbtds["jtbd-1"] == ports.Jtbd(
            jtbd_id="jtbd-1", description="design-feature", status="drafting"
        )

    async def test_mark_jtbd_drafting_answers_the_jtbd_id_it_saved(self) -> None:
        jtbd_actions = application.JtbdActions(FakeJtbdStore())

        mark_jtbd_drafting_response = await jtbd_actions.mark_jtbd_drafting(
            relays.MarkJtbdDraftingRequest(jtbd_id="jtbd-1", description="design-feature", status="drafting")
        )

        assert mark_jtbd_drafting_response.jtbd_id == "jtbd-1"
