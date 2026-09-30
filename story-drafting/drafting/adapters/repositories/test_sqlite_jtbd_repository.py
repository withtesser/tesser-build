# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import pathlib

import pytest

import drafting.adapters.repositories as repositories
import drafting.application.ports as ports


class TestSqliteJtbdRepository:

    async def test_a_saved_jtbd_is_loaded_in_a_later_transaction(self, tmp_path: pathlib.Path) -> None:
        sqlite_jtbd_repository = repositories.SqliteJtbdRepository(location=str(tmp_path / "sqlite_jtbd_repository"))
        jtbd = ports.Jtbd(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away", stories=(ports.Story(given="a job to be done", when="I submit it", then="it is drafting its stories", state="drafted"),))

        async with sqlite_jtbd_repository.transaction() as jtbd_repository:
            await jtbd_repository.save_jtbd(ports.SaveJtbdRequest(jtbd=jtbd))
        async with sqlite_jtbd_repository.transaction() as jtbd_repository:
            load_jtbd_response = await jtbd_repository.load_jtbd(ports.LoadJtbdRequest(jtbd_id="jtbd-1"))

        assert load_jtbd_response.jtbd == jtbd

    async def test_a_jtbd_never_saved_is_not_loaded(self, tmp_path: pathlib.Path) -> None:
        sqlite_jtbd_repository = repositories.SqliteJtbdRepository(location=str(tmp_path / "sqlite_jtbd_repository"))

        async with sqlite_jtbd_repository.transaction() as jtbd_repository:
            with pytest.raises(KeyError):
                await jtbd_repository.load_jtbd(ports.LoadJtbdRequest(jtbd_id="jtbd-1"))

    async def test_two_stores_hold_two_separate_sets_of_jtbds(self, tmp_path: pathlib.Path) -> None:
        sqlite_jtbd_repository = repositories.SqliteJtbdRepository(location=str(tmp_path / "sqlite_jtbd_repository"))
        other_store = repositories.SqliteJtbdRepository(location=str(tmp_path / "other"))

        async with sqlite_jtbd_repository.transaction() as jtbd_repository:
            await jtbd_repository.save_jtbd(ports.SaveJtbdRequest(jtbd=ports.Jtbd(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away", stories=(ports.Story(given="a job to be done", when="I submit it", then="it is drafting its stories", state="drafted"),))))
        async with other_store.transaction() as jtbd_repository:
            with pytest.raises(KeyError):
                await jtbd_repository.load_jtbd(ports.LoadJtbdRequest(jtbd_id="jtbd-1"))
