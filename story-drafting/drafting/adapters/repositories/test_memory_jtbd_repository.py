# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import pytest

import drafting.adapters.repositories as repositories
import drafting.application.ports as ports


class TestMemoryJtbdStore:

    async def test_a_saved_jtbd_is_loaded_in_a_later_transaction(self) -> None:
        memory_jtbd_store = repositories.MemoryJtbdStore()
        jtbd = ports.Jtbd(jtbd_id="jtbd-1", role="a developer", i_want="stories drafted for my work", so_that="I can accept the ones I keep", stories=(ports.StorySpec(given="a job to be done", when="I submit it", then="I see it drafting", state="drafted"),))

        async with memory_jtbd_store.transaction() as jtbd_repository:
            await jtbd_repository.save_jtbd(ports.SaveJtbdRequest(jtbd=jtbd))
        async with memory_jtbd_store.transaction() as jtbd_repository:
            load_jtbd_response = await jtbd_repository.load_jtbd(ports.LoadJtbdRequest(jtbd_id="jtbd-1"))

        assert load_jtbd_response.jtbd == jtbd

    async def test_a_jtbd_never_saved_is_not_loaded(self) -> None:
        memory_jtbd_store = repositories.MemoryJtbdStore()

        async with memory_jtbd_store.transaction() as jtbd_repository:
            with pytest.raises(KeyError):
                await jtbd_repository.load_jtbd(ports.LoadJtbdRequest(jtbd_id="jtbd-1"))

    async def test_two_stores_hold_two_separate_sets_of_jtbds(self) -> None:
        memory_jtbd_store = repositories.MemoryJtbdStore()
        other_store = repositories.MemoryJtbdStore()

        async with memory_jtbd_store.transaction() as jtbd_repository:
            await jtbd_repository.save_jtbd(ports.SaveJtbdRequest(jtbd=ports.Jtbd(jtbd_id="jtbd-1", role="a developer", i_want="stories drafted for my work", so_that="I can accept the ones I keep", stories=(ports.StorySpec(given="a job to be done", when="I submit it", then="I see it drafting", state="drafted"),))))
        async with other_store.transaction() as jtbd_repository:
            with pytest.raises(KeyError):
                await jtbd_repository.load_jtbd(ports.LoadJtbdRequest(jtbd_id="jtbd-1"))
