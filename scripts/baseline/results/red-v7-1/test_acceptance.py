from __future__ import annotations

import json
import random
import time
import urllib.error as urllib_error
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingAJtbd:

    def test_a_jtbd_checked_on_right_away_is_drafting(self) -> None:
        job = random.choice(
            (
                "design a login page, get my sign-off, then build it",
                "plan a data migration, get my sign-off, then run it",
                "draft an API, get my sign-off, then implement it",
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
        check_status_status = 0
        status: dict[str, object] = {}
        while check_status_status != 200 and time.monotonic() < deadline:
            try:
                with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                    check_status_status = answer.status
                    status = json.loads(answer.read())
            except urllib_error.HTTPError as error:
                check_status_status = error.code
                error.close()
                time.sleep(0.2)

        assert (submit_jtbd_status, check_status_status) == (201, 200)
        assert (status.get("jtbd_id"), status.get("job"), status.get("step")) == (jtbd_id, job, "drafting")
