from __future__ import annotations

import json
import urllib.request as urllib_request
import uuid

import tesser.testing as ts


class TestSubmittingAJobToBeDone:

    def test_a_submitted_job_to_be_done_answers_201_with_its_jtbd_id_and_status_drafting_stories(self) -> None:
        submit = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps(
                {
                    "role": "a developer working through a multi-step piece of work with an agent",
                    "i_want": "the steps and the checkpoints where I weigh in to be fixed in advance " + uuid.uuid4().hex,
                    "so_that": "I can step away, come back, and pick up at the step we were on",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )

        with urllib_request.urlopen(submit, timeout=30) as answer:
            status = answer.status
            submitted = json.loads(answer.read())

        assert status == 201
        assert isinstance(submitted.get("jtbd_id"), str) and submitted["jtbd_id"]
        assert submitted.get("status") == "drafting_stories"
