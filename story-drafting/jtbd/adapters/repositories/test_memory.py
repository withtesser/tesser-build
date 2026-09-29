from __future__ import annotations

import jtbd.adapters.repositories as repositories
import jtbd.application.ports as ports


class TestMemoryJtbdStore:

    async def test_a_saved_jtbd_is_loaded_in_a_later_transaction(self) -> None:
        memory_jtbd_store = repositories.MemoryJtbdStore()

        async with memory_jtbd_store.transaction() as jtbd_repository:
            save_jtbd_response = await jtbd_repository.save_jtbd(
                ports.SaveJtbdRequest(jtbd_id="jtbd-1", description="design-feature", status="drafting")
            )
        async with memory_jtbd_store.transaction() as jtbd_repository:
            load_jtbd_response = await jtbd_repository.load_jtbd(
                ports.LoadJtbdRequest(jtbd_id="jtbd-1")
            )

        assert save_jtbd_response == ports.SaveJtbdResponse(jtbd_id="jtbd-1")
        assert load_jtbd_response.jbtds == (
            ports.Jtbd(jtbd_id="jtbd-1", description="design-feature", status="drafting"),
        )

    async def test_a_jtbd_never_saved_loads_nothing(self) -> None:
        memory_jtbd_store = repositories.MemoryJtbdStore()

        async with memory_jtbd_store.transaction() as jtbd_repository:
            load_jtbd_response = await jtbd_repository.load_jtbd(
                ports.LoadJtbdRequest(jtbd_id="jtbd-1")
            )

        assert load_jtbd_response.jbtds == ()

    async def test_two_stores_hold_two_separate_jbtds(self) -> None:
        memory_jtbd_store = repositories.MemoryJtbdStore()
        other_store = repositories.MemoryJtbdStore()

        async with memory_jtbd_store.transaction() as jtbd_repository:
            await jtbd_repository.save_jtbd(
                ports.SaveJtbdRequest(jtbd_id="jtbd-1", description="design-feature", status="drafting")
            )
        async with other_store.transaction() as jtbd_repository:
            load_jtbd_response = await jtbd_repository.load_jtbd(
                ports.LoadJtbdRequest(jtbd_id="jtbd-1")
            )

        assert load_jtbd_response.jbtds == ()
