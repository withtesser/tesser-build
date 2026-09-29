from __future__ import annotations

import json
import random
import time
import urllib.request as urllib_request

import tesser.testing as ts


class TestDraftingStories:

    def test_a_started_run_waits_for_a_pick_among_its_drafted_stories(self) -> None:
        job = random.choice(("Plan a trip", "File my taxes", "Onboard a new hire"))
        open_run = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/runs",
            data=json.dumps(
                {
                    "job": job,
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )

        with urllib_request.urlopen(open_run, timeout=30) as answer:
            open_run_status = answer.status
            run_id = json.loads(answer.read())["run_id"]
        for _ in range(40):
            with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/runs/{run_id}", timeout=30) as answer:
                get_run_status = answer.status
                get_run = json.loads(answer.read())
            if get_run.get("stage") == "awaiting_pick":
                break
            time.sleep(0.25)

        assert (open_run_status, get_run_status) == (201, 200)
        assert get_run["job"] == job
        assert get_run.get("stage") == "awaiting_pick"
        assert len(get_run.get("stories", [])) > 0
        assert get_run.get("accepted_story") is None
