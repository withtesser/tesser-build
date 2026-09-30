from __future__ import annotations

import json
import time
import urllib.request as urllib_request

import tesser.testing as ts


class TestReadJtbd:

    def test_a_drafted_jtbd_is_read_awaiting_story_acceptance_with_its_stories_drafted(self) -> None:
        host = ts.served("STORY_DRAFTING_HOST")
        submit = urllib_request.Request(
            f"{host}/jtbds",
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
        with urllib_request.urlopen(submit, timeout=30) as submitted_answer:
            jtbd_id = json.loads(submitted_answer.read())["jtbd_id"]
        status = 0
        read = {}
        for _ in range(50):
            with urllib_request.urlopen(f"{host}/jtbds/{jtbd_id}", timeout=30) as answer:
                status = answer.status
                read = json.loads(answer.read())
            if read["status"] == "awaiting_story_acceptance":
                break
            time.sleep(0.1)
        assert status == 200
        assert read["status"] == "awaiting_story_acceptance"
        assert len(read["stories"]) >= 1
        for story in read["stories"]:
            assert story["given"] != ""
            assert story["when"] != ""
            assert story["then"] != ""
            assert story["state"] == "drafted"
