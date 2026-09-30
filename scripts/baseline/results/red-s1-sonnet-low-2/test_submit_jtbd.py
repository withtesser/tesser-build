from __future__ import annotations

import json
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmitJtbd:

    def test_a_submitted_jtbd_answers_201_with_its_jtbd_id_and_status_drafting_stories(self) -> None:
        submit = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps(
                {
                    "role": "a developer",
                    "i_want": "my stories drafted",
                    "so_that": "I can weigh in on them",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(submit, timeout=30) as answer:
            status = answer.status
            submitted = json.loads(answer.read())
        assert status == 201
        assert isinstance(submitted["jtbd_id"], str)
        assert submitted["jtbd_id"] != ""
        assert submitted["status"] == "drafting_stories"
