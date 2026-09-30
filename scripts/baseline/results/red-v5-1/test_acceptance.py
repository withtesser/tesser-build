from __future__ import annotations

import json
import random
import time
import urllib.error as urllib_error
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingJtbds:

    def test_a_submitted_jtbd_stops_at_the_pick_with_drafts_and_none_picked(self) -> None:
        job = random.choice(
            (
                "Design the export, get my sign-off, then build it",
                "Plan the migration, get my sign-off, then run it",
                "Sketch the onboarding, get my sign-off, then ship it",
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
        deadline = time.monotonic() + 30
        come_back_status = 0
        come_back: dict[str, object] = {}
        while come_back_status != 200 and time.monotonic() < deadline:
            try:
                with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                    come_back_status = answer.status
                    come_back = json.loads(answer.read())
            except urllib_error.HTTPError as error:
                come_back_status = error.code
                error.close()
                time.sleep(0.2)

        assert (submit_jtbd_status, come_back_status) == (201, 200)
        assert come_back["job"] == job

        at_the_pick: dict[str, object] = come_back
        while at_the_pick.get("step") != "pick" and time.monotonic() < deadline:
            time.sleep(0.2)
            with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                at_the_pick = json.loads(answer.read())
        drafts = at_the_pick.get("drafts")

        assert (
            at_the_pick.get("step"),
            isinstance(drafts, list) and len(drafts) >= 1,
            at_the_pick.get("picked_draft"),
        ) == ("pick", True, None)
