from __future__ import annotations

import json
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmitAndCheckStatus:

    def test_submitted_jtbd_status_is_drafting(self) -> None:
        submit_jtbd = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps(
                {
                    "status": "waiting_for_pick",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )

        with urllib_request.urlopen(submit_jtbd, timeout=30) as answer:
            submit_jtbd_status = answer.status
            jtbd_id = json.loads(answer.read())["jtbd_id"]
        with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
            get_status_status = answer.status
            get_status = json.loads(answer.read())

        assert (submit_jtbd_status, get_status_status) == (201, 200)
        assert get_status["status"] == "drafting"
