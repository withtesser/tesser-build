from __future__ import annotations

import json
import random
import time
import urllib.error as urllib_error
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingJtbds:

    def test_a_submitted_jtbd_stops_at_the_pick_with_drafts_to_pick_from(self) -> None:
        job = random.choice(
            (
                "Design a billing page, get my sign-off, then build it",
                "Plan a data migration, get my sign-off, then run it",
                "Sketch an onboarding flow, get my sign-off, then ship it",
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
        try:
            with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                came_back_right_away_status = answer.status
        except urllib_error.HTTPError as error:
            came_back_right_away_status = error.code
            error.close()
        deadline = time.monotonic() + 30
        came_back_status = 0
        came_back: dict[str, object] = {}
        while not (came_back_status == 200 and came_back.get("step") == "pick") and time.monotonic() < deadline:
            try:
                with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                    came_back_status = answer.status
                    came_back = json.loads(answer.read())
            except urllib_error.HTTPError as error:
                came_back_status = error.code
                error.close()
            time.sleep(0.2)
        drafts = came_back.get("drafts")

        assert (
            submit_jtbd_status,
            came_back_right_away_status,
            came_back_status,
            came_back.get("job"),
            came_back.get("step"),
            isinstance(drafts, list) and len(drafts) >= 1,
            came_back.get("picked_draft", "absent"),
        ) == (201, 200, 200, job, "pick", True, None)
