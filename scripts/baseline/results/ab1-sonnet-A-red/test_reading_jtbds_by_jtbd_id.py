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
        created = urllib_request.Request(
            f"{host}/jtbds", data=b'{"role": "a developer", "i_want": "the steps fixed in advance", "so_that": "I can pick up where we left off"}', headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib_request.urlopen(created, timeout=30) as created_answer:
            jtbd_id: str | None = json.loads(created_answer.read())["jtbd_id"]
        assert jtbd_id is not None, "POST /jtbds did not answer a jtbd_id"

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            with urllib_request.urlopen(f"{host}/jtbds/{jtbd_id}", timeout=30) as polled:
                if json.loads(polled.read()).get("status") == "awaiting_story_acceptance":
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
        assert answered["status"] == "awaiting_story_acceptance", f"status is not awaiting_story_acceptance (answered {answered_body!r})"
        assert len(answered["stories"]) >= 1, f"no story (answered {answered_body!r})"
        for story in answered["stories"]:
            assert story["given"] and story["when"] and story["then"], f"a story lacks a given, when, or then (answered {answered_body!r})"
            assert story["state"] == "drafted", f"a story is not drafted (answered {answered_body!r})"
