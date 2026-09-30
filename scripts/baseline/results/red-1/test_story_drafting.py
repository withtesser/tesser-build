from __future__ import annotations

import asyncio

import app as app
import drafting.client as drafting_client


class TestStoryDrafting:

    async def test_drafted_stories_wait_for_the_developers_pick_with_none_accepted(self) -> None:
        story_drafting_app = app.load()
        try:
            draft_stories_response = await story_drafting_app.drafting.client.draft_stories(
                drafting_client.DraftStoriesRequest(
                    job=(
                        "When I'm working through a multi-step piece of work with an agent, "
                        "I want the steps and the checkpoints where I weigh in to be fixed in advance "
                        "and to survive across sessions, so I can step away and pick up where we were."
                    )
                )
            )
            get_drafting_request = drafting_client.GetDraftingRequest(
                drafting_id=draft_stories_response.drafting_id
            )
            get_drafting_response = await story_drafting_app.drafting.client.get_drafting(get_drafting_request)
            for _ in range(100):
                if get_drafting_response.drafting.step != "drafting":
                    break
                await asyncio.sleep(0.1)
                get_drafting_response = await story_drafting_app.drafting.client.get_drafting(get_drafting_request)
        finally:
            await story_drafting_app.close()

        assert get_drafting_response.drafting.drafting_id == draft_stories_response.drafting_id
        assert get_drafting_response.drafting.step == "awaiting_pick"
        assert get_drafting_response.drafting.stories != ()
        assert get_drafting_response.drafting.accepted_stories == ()
