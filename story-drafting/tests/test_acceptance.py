from __future__ import annotations

import json
import random
import urllib.request as urllib_request

import tesser.testing as ts


class TestStartingRuns:

    def test_a_started_run_waits_for_a_pick_among_drafted_stories(self) -> None:
        job = random.choice(
            (
                "When I plan a trip with friends, I want one itinerary we all agreed on, so I can book it",
                "When I ship a release, I want the changelog drafted from what merged, so I can publish on time",
                "When I hire a designer, I want the brief settled before interviews, so I can compare candidates",
            )
        )
        begin_run = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/runs",
            data=json.dumps(
                {
                    "job": job,
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )

        with urllib_request.urlopen(begin_run, timeout=30) as answer:
            begin_run_status = answer.status
            run_id = json.loads(answer.read())["run_id"]
        with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/runs/{run_id}", timeout=30) as answer:
            get_run_status = answer.status
            get_run = json.loads(answer.read())

        assert (begin_run_status, get_run_status) == (201, 200)
        assert (get_run["run_id"], get_run["job"]) == (run_id, job)
        assert {
            "status": get_run.get("status"),
            "has_drafted_stories": bool(get_run.get("stories")),
            "accepted_story": get_run.get("accepted_story"),
        } == {
            "status": "awaiting_pick",
            "has_drafted_stories": True,
            "accepted_story": None,
        }
