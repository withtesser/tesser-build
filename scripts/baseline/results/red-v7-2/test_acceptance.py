from __future__ import annotations

import json
import random
import time
import urllib.error as urllib_error
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingAJtbd:

    def test_a_just_submitted_jtbd_is_drafting(self) -> None:
        job = random.choice(
            (
                "design an api, get my sign-off, then build it",
                "plan a release, get my sign-off, then ship it",
                "sketch a data model, get my sign-off, then migrate it",
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
        assert (status["jtbd_id"], status["job"]) == (jtbd_id, job)
        assert status.get("step") == "drafting"
