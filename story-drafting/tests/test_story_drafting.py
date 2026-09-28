from __future__ import annotations

import json
import time
import urllib.error as urllib_error
import urllib.request as urllib_request
import uuid

import tesser.testing as ts


class TestStartingTheStoryDraftingSkill:

    def test_a_started_run_waits_for_the_pick_with_drafted_stories_and_none_accepted(self) -> None:
        run_id = str(uuid.uuid4())
        job = (
            "When I'm working through a multi-step piece of work with an agent, I want the steps and "
            "the checkpoints where I weigh in fixed in advance and surviving across sessions, so I can "
            "step away and pick up at the step we were on."
        )
        start = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/runs",
            data=json.dumps({"run_id": run_id, "job": job}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib_request.urlopen(start, timeout=30) as answer:
            started_status = answer.status
            started = json.loads(answer.read())
        run: dict[str, object] = {}
        for _ in range(100):
            try:
                with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/runs/{run_id}", timeout=30) as answer:
                    run = json.loads(answer.read())
                if run["stage"] == "awaiting_pick":
                    break
            except urllib_error.HTTPError as e:
                if e.code != 404:
                    raise
            time.sleep(0.1)
        assert started_status == 202
        assert started == {"run_id": run_id}
        assert run, "the host never read the started run back"
        assert run["run_id"] == run_id
        assert run["job"] == job
        assert run["stage"] == "awaiting_pick"
        assert run["stories"] != []
        assert run["accepted_stories"] == []
