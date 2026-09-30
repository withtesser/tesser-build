from __future__ import annotations

import json
import time
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittedJtbd:

    def test_s_1_a_1_submitting_a_jtbd_answers_201_with_its_jtbd_id_and_status_drafting_stories(self) -> None:
        submit = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps(
                {
                    "role": "a developer",
                    "i_want": "my steps fixed in advance",
                    "so_that": "I can step away",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(submit, timeout=30) as answer:
            status = answer.status
            submitted = json.loads(answer.read())
        assert status == 201
        assert submitted["jtbd_id"]
        assert submitted["status"] == "drafting_stories"

    def test_s_2_a_1_a_drafted_jtbd_is_read_awaiting_story_acceptance_with_drafted_stories(self) -> None:
        host = ts.served("STORY_DRAFTING_HOST")
        submit = urllib_request.Request(
            f"{host}/jtbds",
            data=json.dumps(
                {
                    "role": "a developer",
                    "i_want": "my steps fixed in advance",
                    "so_that": "I can step away",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(submit, timeout=30) as answer:
            jtbd_id = json.loads(answer.read())["jtbd_id"]
        deadline = time.monotonic() + 8
        while True:
            with urllib_request.urlopen(f"{host}/jtbds/{jtbd_id}", timeout=30) as answer:
                status = answer.status
                read = json.loads(answer.read())
            if read["status"] == "awaiting_story_acceptance" or time.monotonic() > deadline:
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
