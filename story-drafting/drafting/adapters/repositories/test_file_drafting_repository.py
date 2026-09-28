from __future__ import annotations

import pathlib

import drafting.adapters.repositories as repositories
import drafting.application.ports as ports


class TestFileDraftingStore:

    async def test_a_saved_drafting_is_loaded_back_whole_by_another_store_over_the_same_directory(
        self, tmp_path: pathlib.Path
    ) -> None:
        async with repositories.FileDraftingStore(str(tmp_path)).transaction() as drafting_repository:
            issue_drafting_id_response = await drafting_repository.issue_drafting_id(ports.IssueDraftingIdRequest())
            await drafting_repository.save_drafting(
                ports.SaveDraftingRequest(
                    drafting_row=ports.DraftingRow(
                        drafting_id=issue_drafting_id_response.drafting_id,
                        job="a job",
                        step="awaiting_pick",
                        stories=(ports.StoryRow(story_id="1", text="first"), ports.StoryRow(story_id="2", text="second")),
                        accepted_stories=(ports.StoryRow(story_id="2", text="second"),),
                    )
                )
            )

        async with repositories.FileDraftingStore(str(tmp_path)).transaction() as drafting_repository:
            load_drafting_response = await drafting_repository.load_drafting(
                ports.LoadDraftingRequest(drafting_id=issue_drafting_id_response.drafting_id)
            )

        assert load_drafting_response == ports.LoadDraftingResponse(
            outcome=ports.LoadDraftingOutcome.FOUND,
            drafting_rows=(
                ports.DraftingRow(
                    drafting_id=issue_drafting_id_response.drafting_id,
                    job="a job",
                    step="awaiting_pick",
                    stories=(ports.StoryRow(story_id="1", text="first"), ports.StoryRow(story_id="2", text="second")),
                    accepted_stories=(ports.StoryRow(story_id="2", text="second"),),
                ),
            ),
        )

    async def test_a_later_save_of_a_drafting_replaces_the_earlier_one(self, tmp_path: pathlib.Path) -> None:
        async with repositories.FileDraftingStore(str(tmp_path)).transaction() as drafting_repository:
            await drafting_repository.save_drafting(
                ports.SaveDraftingRequest(
                    drafting_row=ports.DraftingRow(
                        drafting_id="d1", job="a job", step="drafting", stories=(), accepted_stories=()
                    )
                )
            )
            await drafting_repository.save_drafting(
                ports.SaveDraftingRequest(
                    drafting_row=ports.DraftingRow(
                        drafting_id="d1",
                        job="a job",
                        step="awaiting_pick",
                        stories=(ports.StoryRow(story_id="1", text="first"),),
                        accepted_stories=(),
                    )
                )
            )
            load_drafting_response = await drafting_repository.load_drafting(ports.LoadDraftingRequest(drafting_id="d1"))

        assert [drafting_row.step for drafting_row in load_drafting_response.drafting_rows] == ["awaiting_pick"]
        assert sorted(path.name for path in tmp_path.iterdir()) == ["d1.json"]

    async def test_issued_drafting_ids_differ(self, tmp_path: pathlib.Path) -> None:
        async with repositories.FileDraftingStore(str(tmp_path)).transaction() as drafting_repository:
            first = await drafting_repository.issue_drafting_id(ports.IssueDraftingIdRequest())
            second = await drafting_repository.issue_drafting_id(ports.IssueDraftingIdRequest())

        assert first.drafting_id != second.drafting_id

    async def test_a_drafting_never_saved_is_not_found(self, tmp_path: pathlib.Path) -> None:
        async with repositories.FileDraftingStore(str(tmp_path)).transaction() as drafting_repository:
            load_drafting_response = await drafting_repository.load_drafting(
                ports.LoadDraftingRequest(drafting_id="never-saved")
            )

        assert load_drafting_response == ports.LoadDraftingResponse(
            outcome=ports.LoadDraftingOutcome.NOT_FOUND, drafting_rows=()
        )

    async def test_an_id_naming_a_path_outside_the_directory_is_not_found(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "outside.json").write_text("{}")
        (tmp_path / "inside").mkdir()

        async with repositories.FileDraftingStore(str(tmp_path / "inside")).transaction() as drafting_repository:
            load_drafting_response = await drafting_repository.load_drafting(
                ports.LoadDraftingRequest(drafting_id="../outside")
            )

        assert load_drafting_response.outcome is ports.LoadDraftingOutcome.NOT_FOUND
