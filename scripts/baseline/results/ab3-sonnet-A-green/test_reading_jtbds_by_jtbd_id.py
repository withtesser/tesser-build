# pragma: tesser-agent-owned; generated once as a skeleton, the agent owns it from here
from __future__ import annotations

import json
import time
import urllib.error as urllib_error
import urllib.request as urllib_request


class TestReadingJtbdsByJtbdId:

    def test_s_2_a_1(self, host: str) -> None:
        created = urllib_request.Request(
            f"{host}/jtbds", data=b'{"role": "a developer", "i_want": "to keep my place", "so_that": "I can step away"}', headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib_request.urlopen(created, timeout=30) as created_answer:
            jtbd_id: str | None = json.loads(created_answer.read())["jtbd_id"]
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            polled = urllib_request.Request(f"{host}/jtbds/{jtbd_id}", method="GET")
            with urllib_request.urlopen(polled, timeout=30) as polled_answer:
                if json.loads(polled_answer.read()).get("status") == "awaiting_story_acceptance":
                    break
            time.sleep(0.5)
        assert jtbd_id is not None, 'write the given of s-2-a-1: I have created a job to be done with POST /jtbds, and its stories have been drafted'
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
        assert answered["status"] == "awaiting_story_acceptance", f"(answered {answered_body!r})"
        stories = answered["stories"]
        assert len(stories) >= 1, f"no stories (answered {answered_body!r})"
        for story in stories:
            assert story["given"] and story["when"] and story["then"], f"(answered {answered_body!r})"
            assert story["state"] == "drafted", f"(answered {answered_body!r})"
