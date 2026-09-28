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
