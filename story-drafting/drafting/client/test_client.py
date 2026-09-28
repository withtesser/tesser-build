from __future__ import annotations

import drafting.client as client


class TestDrafting:

    def test_a_drafting_carries_its_stories_and_the_ones_accepted(self) -> None:
        drafted_story = client.DraftedStory(story_id="s1", text="As a developer, I want ...")

        drafting = client.Drafting(
            drafting_id="d1", step="awaiting_pick", stories=(drafted_story,), accepted_stories=()
        )

        assert (drafting.drafting_id, drafting.step, drafting.stories, drafting.accepted_stories) == (
            "d1",
            "awaiting_pick",
            (drafted_story,),
            (),
        )


class TestDraftingRejected:

    def test_a_rejection_carries_its_code_and_message(self) -> None:
        drafting_rejected = client.DraftingRejected("empty_job", "a job to be done says what the job is")

        assert (drafting_rejected.code, drafting_rejected.message) == (
            "empty_job",
            "a job to be done says what the job is",
        )


class TestDraftingNotFound:

    def test_a_drafting_that_was_not_found_carries_its_message(self) -> None:
        drafting_not_found = client.DraftingNotFound("no drafting 'd1'")

        assert drafting_not_found.message == "no drafting 'd1'"


class TestErrors:

    def test_the_declared_set_names_every_error_the_client_raises(self) -> None:
        raised = {
            name
            for name, value in vars(client).items()
            if isinstance(value, type) and issubclass(value, Exception)
        }

        assert {error.__name__ for error in client.ERRORS} == raised
