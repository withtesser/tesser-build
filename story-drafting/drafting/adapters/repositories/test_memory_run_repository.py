from __future__ import annotations

import drafting.adapters.repositories as repositories
import drafting.application.ports as ports


class TestMemoryRunRepository:

    async def test_a_saved_run_is_found_with_what_it_was_saved_with(self) -> None:
        memory_run_repository = repositories.MemoryRunRepository()
        save_run_response = await memory_run_repository.save_run(
            ports.SaveRunRequest(run_id="r1", job="a job", stage="drafting", stories=())
        )
        get_run_response = await memory_run_repository.get_run(ports.GetRunRequest(run_id="r1"))
        assert save_run_response.run_id == "r1"
        assert get_run_response.outcome is ports.GetRunOutcome.FOUND
        assert [(run.run_id, run.job, run.stage) for run in get_run_response.runs] == [("r1", "a job", "drafting")]

    async def test_a_run_never_saved_is_not_found(self) -> None:
        get_run_response = await repositories.MemoryRunRepository().get_run(ports.GetRunRequest(run_id="r1"))
        assert get_run_response.outcome is ports.GetRunOutcome.NOT_FOUND
        assert get_run_response.runs == ()

    async def test_saving_a_run_again_replaces_it_with_its_stories_and_none_accepted(self) -> None:
        memory_run_repository = repositories.MemoryRunRepository()
        await memory_run_repository.save_run(ports.SaveRunRequest(run_id="r1", job="a job", stage="drafting", stories=()))
        await memory_run_repository.save_run(
            ports.SaveRunRequest(run_id="r1", job="a job", stage="awaiting_pick", stories=("a story", "another story"))
        )
        get_run_response = await memory_run_repository.get_run(ports.GetRunRequest(run_id="r1"))
        assert [run.stage for run in get_run_response.runs] == ["awaiting_pick"]
        assert [[story.text for story in run.stories] for run in get_run_response.runs] == [["a story", "another story"]]
        assert [run.accepted_stories for run in get_run_response.runs] == [()]

    async def test_a_closed_repository_holds_nothing(self) -> None:
        memory_run_repository = repositories.MemoryRunRepository()
        await memory_run_repository.save_run(ports.SaveRunRequest(run_id="r1", job="a job", stage="drafting", stories=()))
        memory_run_repository.close()
        get_run_response = await memory_run_repository.get_run(ports.GetRunRequest(run_id="r1"))
        assert get_run_response.outcome is ports.GetRunOutcome.NOT_FOUND
