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
                "Design a login page, get my sign-off, then build it",
                "Plan a data migration, get my sign-off, then run it",
                "Sketch an API, get my sign-off, then implement it",
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
        get_jtbd_status = 0
        get_jtbd: dict[str, object] = {}
        while get_jtbd_status != 200 and time.monotonic() < deadline:
            try:
                with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                    get_jtbd_status = answer.status
                    get_jtbd = json.loads(answer.read())
            except urllib_error.HTTPError as error:
                get_jtbd_status = error.code
                error.close()
                time.sleep(0.2)

        assert (submit_jtbd_status, get_jtbd_status) == (201, 200)
        assert get_jtbd["job"] == job

        deadline = time.monotonic() + 30
        while get_jtbd["step"] != "pick" and time.monotonic() < deadline:
            time.sleep(0.2)
            with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                get_jtbd = json.loads(answer.read())

        assert get_jtbd["step"] == "pick"
        assert isinstance(get_jtbd["draft_count"], int) and get_jtbd["draft_count"] >= 1
        assert get_jtbd["picked_draft"] == ""
