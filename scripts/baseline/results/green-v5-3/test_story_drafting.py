from __future__ import annotations

import json
import time
import urllib.request as urllib_request

import tesser.testing as ts


class TestServedApp:

    def test_s_1_a_1_a_submitted_job_to_be_done_answers_201_with_its_id_and_drafting_stories(self) -> None:
        submit = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps(
                {
                    "role": "a developer",
                    "i_want": "my steps fixed in advance",
                    "so_that": "I can pick up where we left off",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib_request.urlopen(submit, timeout=30) as answer:
            status = answer.status
            submitted = json.loads(answer.read())
        assert status == 201
        assert submitted["jtbd_id"]
        assert submitted["status"] == "drafting_stories"

    def test_s_2_a_1_a_drafted_job_to_be_done_answers_200_with_drafted_stories_awaiting_acceptance(self) -> None:
        host = ts.served("STORY_DRAFTING_HOST")
        submit = urllib_request.Request(
            f"{host}/jtbds",
            data=json.dumps(
                {
                    "role": "a developer",
                    "i_want": "my steps fixed in advance",
                    "so_that": "I can pick up where we left off",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib_request.urlopen(submit, timeout=30) as answer:
            jtbd_id = json.loads(answer.read())["jtbd_id"]
        status = 0
        read = {}
        for _ in range(20):
            with urllib_request.urlopen(f"{host}/jtbds/{jtbd_id}", timeout=30) as answer:
                status = answer.status
                read = json.loads(answer.read())
            if read["status"] == "awaiting_story_acceptance":
                break
            time.sleep(0.25)
        assert status == 200
        assert read["status"] == "awaiting_story_acceptance"
        assert len(read["stories"]) >= 1
        for story in read["stories"]:
            assert story["given"]
            assert story["when"]
            assert story["then"]
            assert story["state"] == "drafted"
