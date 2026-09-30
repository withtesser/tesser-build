# pragma: tesser-agent-owned; generated once as a skeleton, the agent owns it from here
from __future__ import annotations

import json
import time
import urllib.error as urllib_error
import urllib.request as urllib_request

import tesser.testing as ts


class TestReadingJtbdsByJtbdId:

    def test_s_2_a_1(self) -> None:
        host = ts.served("STORY_DRAFTING_HOST")
        create = urllib_request.Request(
            f"{host}/jtbds",
            data=b'{"role": "a developer", "i_want": "stories drafted for my work", "so_that": "I can accept the ones I keep"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(create, timeout=30) as created:
            jtbd_id: str | None = json.loads(created.read())["jtbd_id"]
        assert jtbd_id is not None, "POST /jtbds answered no jtbd_id"
        for _ in range(20):
            with urllib_request.urlopen(f"{host}/jtbds/{jtbd_id}", timeout=30) as polled:
                if json.loads(polled.read())["stories"]:
                    break
            time.sleep(0.5)
        request = urllib_request.Request(
            f"{host}/jtbds/{jtbd_id}", data=None, headers={"Content-Type": "application/json"}, method="GET"
        )

        try:
            with urllib_request.urlopen(request, timeout=30) as answer:
                status, answered_body = answer.status, answer.read()
        except urllib_error.HTTPError as error:
            status, answered_body = error.code, error.read()

        assert status == 200
        answered = json.loads(answered_body)
        assert answered["status"] == "awaiting_story_acceptance", answered
        assert len(answered["stories"]) >= 1, answered
        for story in answered["stories"]:
            assert story["given"] and story["when"] and story["then"], answered
            assert story["state"] == "drafted", answered
