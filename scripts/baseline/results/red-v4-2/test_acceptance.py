from __future__ import annotations

import json
import random
import time
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingJtbds:

    def test_a_submitted_jtbd_stops_at_the_pick_with_drafts_and_none_picked(self) -> None:
        job = random.choice(
            (
                "Design a feature, get my sign-off, then build it",
                "Plan a migration, review it with me, then run it",
                "Sketch an API, agree it with me, then implement it",
            )
        )
        submit_jtbd = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps({"job": job}).encode(),
            headers={"Content-Type": "application/json"},
        )

        with urllib_request.urlopen(submit_jtbd, timeout=30) as answer:
            submit_jtbd_status = answer.status
            jtbd_id = json.loads(answer.read())["jtbd_id"]
        with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
            come_back_right_away_status = answer.status
            come_back_right_away = json.loads(answer.read())
        come_back_to_jtbd = come_back_right_away
        deadline = time.monotonic() + 30
        while come_back_to_jtbd.get("step") == "drafting" and time.monotonic() < deadline:
            time.sleep(0.2)
            with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                come_back_to_jtbd = json.loads(answer.read())

        assert (submit_jtbd_status, come_back_right_away_status) == (201, 200)
        assert (come_back_right_away["jtbd_id"], come_back_right_away["job"]) == (jtbd_id, job)
        assert {
            "step": come_back_to_jtbd.get("step"),
            "drafts to pick from": bool(come_back_to_jtbd.get("drafts")),
            "picked_draft": come_back_to_jtbd.get("picked_draft", "absent"),
        } == {
            "step": "pick",
            "drafts to pick from": True,
            "picked_draft": None,
        }
