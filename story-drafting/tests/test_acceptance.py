from __future__ import annotations

import json
import random
import time
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingJtbds:

    def test_a_submitted_jtbd_stops_at_the_pick_with_drafts_and_none_picked(self) -> None:
        situation = random.choice(
            (
                "I am designing a checkout flow with an agent",
                "I am planning a data migration with an agent",
                "I am building a CLI with an agent",
            )
        )
        submit_jtbd = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps(
                {
                    "situation": situation,
                    "motivation": "the steps and my checkpoints fixed in advance",
                    "outcome": "I can step away and resume where we were",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )

        with urllib_request.urlopen(submit_jtbd, timeout=30) as answer:
            submit_jtbd_status = answer.status
            jtbd_id = json.loads(answer.read())["jtbd_id"]
        with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
            right_away_status = answer.status
            right_away = json.loads(answer.read())
        came_back = right_away
        deadline = time.monotonic() + 20
        while came_back.get("step") != "pick" and time.monotonic() < deadline:
            time.sleep(0.5)
            with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                came_back = json.loads(answer.read())

        assert (submit_jtbd_status, right_away_status, right_away["jtbd_id"]) == (201, 200, jtbd_id)
        assert (
            came_back.get("step"),
            len(came_back.get("drafts", [])) > 0,
            came_back.get("picked_draft", "no picked_draft in the answer"),
        ) == ("pick", True, None)
