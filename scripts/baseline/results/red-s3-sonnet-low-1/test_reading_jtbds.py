# pragma: tesser-agent-owned; generated once as a skeleton, the agent owns it from here
from __future__ import annotations

import json
import time
import urllib.error as urllib_error
import urllib.request as urllib_request

import tesser.testing as ts


class TestReadingJtbds:

    def test_s_2_a_1(self) -> None:
        host = ts.served("STORY_DRAFTING_HOST")
        with urllib_request.urlopen(
            urllib_request.Request(
                f"{host}/jtbds", data=b'{"role": "a developer", "i_want": "my steps fixed in advance", "so_that": "I can step away and return"}', headers={"Content-Type": "application/json"}, method="POST"
            ),
            timeout=30,
        ) as answer:
            answered = json.loads(answer.read())
        given_jtbd_id = answered["jtbd_id"]
        for _ in range(40):
            with urllib_request.urlopen(
                urllib_request.Request(
                    f"{host}/jtbds/{given_jtbd_id}", data=None, headers={"Content-Type": "application/json"}, method="GET"
                ),
                timeout=30,
            ) as answer:
                answered = json.loads(answer.read())
            if answered.get("status") == 'awaiting_story_acceptance':
                break
            time.sleep(0.25)
        request = urllib_request.Request(
            f"{host}/jtbds/{given_jtbd_id}", data=None, headers={"Content-Type": "application/json"}, method="GET"
        )

        try:
            with urllib_request.urlopen(request, timeout=30) as answer:
                status, answered_body = answer.status, answer.read()
        except urllib_error.HTTPError as error:
            status, answered_body = error.code, error.read()

        assert status == 200
        body = json.loads(answered_body)
        assert body["status"] == "awaiting_story_acceptance"
        assert len(body["stories"]) >= 1
        for story in body["stories"]:
            assert story["given"]
            assert story["when"]
            assert story["then"]
            assert story["state"] == "drafted"
