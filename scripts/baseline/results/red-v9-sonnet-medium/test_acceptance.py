from __future__ import annotations

import json
import random
import time
import urllib.error as urllib_error
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingAJtbd:

    def test_a_just_submitted_jtbd_is_drafting(self) -> None:
        situation = random.choice(("multi-step work with an agent", "a design to sign off"))
        submit_jtbd = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps(
                {
                    "situation": situation,
                    "motivation": "the steps and checkpoints fixed in advance",
                    "outcome": "resume at the step we were on",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )

        with urllib_request.urlopen(submit_jtbd, timeout=30) as answer:
            submit_jtbd_status = answer.status
            jtbd_id = json.loads(answer.read())["jtbd_id"]
        deadline = time.monotonic() + 30
        check_jtbd_status = 0
        check_jtbd: dict[str, object] = {}
        while check_jtbd_status != 200 and time.monotonic() < deadline:
            try:
                with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                    check_jtbd_status = answer.status
                    check_jtbd = json.loads(answer.read())
            except urllib_error.HTTPError as error:
                check_jtbd_status = error.code
                error.close()
                time.sleep(0.2)

        assert (submit_jtbd_status, check_jtbd_status) == (201, 200)
        assert check_jtbd.get("step") == "drafting"
