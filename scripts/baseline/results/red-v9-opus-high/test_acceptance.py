from __future__ import annotations

import json
import random
import time
import urllib.error as urllib_error
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingAJtbd:

    def test_a_submitted_jtbd_is_drafting_right_away(self) -> None:
        job = random.choice(
            (
                "When I design a schema, I want my sign-off before the build, so I can step away",
                "When I plan a migration, I want the checkpoints fixed, so I can resume tomorrow",
                "When I write an API, I want the design reviewed first, so I can come back later",
                "When I refactor a module, I want each step agreed, so I can pick up where we left off",
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
        assert status.get("step") == "drafting", f"the first status the host answers for a just-submitted JTBD: {status}"
