from __future__ import annotations

import asyncio

import app as app
import drafting.client as drafting_client


class TestDraftingStoriesForAJob:

    async def test_a_started_run_waits_for_the_pick_with_its_drafted_stories_and_none_accepted(self) -> None:
        job = (
            "When I'm working through a multi-step piece of work with an agent, I want the steps and the checkpoints "
            "where I weigh in to be fixed in advance and to survive across sessions, so I can step away, come back, "
            "and pick up at the step we were on."
        )
        story_drafting_app = app.load()
        try:
            open_run_response = await story_drafting_app.drafting.client.open_run(
                drafting_client.OpenRunRequest(job=job)
            )
            get_run_response = await story_drafting_app.drafting.client.get_run(
                drafting_client.GetRunRequest(run_id=open_run_response.run_id)
            )
            for _ in range(200):
                if get_run_response.run.step != "drafting":
                    break
                await asyncio.sleep(0.05)
                get_run_response = await story_drafting_app.drafting.client.get_run(
                    drafting_client.GetRunRequest(run_id=open_run_response.run_id)
                )
        finally:
            story_drafting_app.close()

        assert get_run_response.run.run_id == open_run_response.run_id
        assert get_run_response.run.job == job
        assert get_run_response.run.step == "awaiting_pick"
        assert get_run_response.run.drafted_stories != ()
        assert get_run_response.run.accepted_stories == ()
