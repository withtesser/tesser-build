# pragma: tesser-agent-owned; generated once as a skeleton, the agent owns it from here
from __future__ import annotations

import json
import time
import urllib.error as urllib_error
import urllib.request as urllib_request


class TestReadingJtbdsByJtbdId:

    def test_s_2_a_1(self, host: str) -> None:
        submitted = {
            "role": "a developer",
            "i_want": "my checkpoints fixed in advance",
            "so_that": "I can step away and come back",
        }
        submitting = urllib_request.Request(
            f"{host}/jtbds", data=json.dumps(submitted).encode(), headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib_request.urlopen(submitting, timeout=30) as submitted_answer:
            assert submitted_answer.status == 201
            jtbd_id: str | None = json.loads(submitted_answer.read())["jtbd_id"]
        assert jtbd_id is not None, 'write the given of s-2-a-1: I have created a job to be done with POST /jtbds, and its stories have been drafted'

        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            polling = urllib_request.Request(f"{host}/jtbds/{jtbd_id}", method="GET")
            try:
                with urllib_request.urlopen(polling, timeout=30) as polled:
                    if json.loads(polled.read()).get("status") == "awaiting_story_acceptance":
                        break
            except urllib_error.HTTPError:
                pass
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
        assert answered["status"] == "awaiting_story_acceptance", f"answered {answered_body!r}"
        stories = answered["stories"]
        assert isinstance(stories, list) and len(stories) >= 1, f"no stories (answered {answered_body!r})"
        for story in stories:
            assert isinstance(story["given"], str) and story["given"] != "", f"a story with no given (answered {answered_body!r})"
            assert isinstance(story["when"], str) and story["when"] != "", f"a story with no when (answered {answered_body!r})"
            assert isinstance(story["then"], str) and story["then"] != "", f"a story with no then (answered {answered_body!r})"
            assert story["state"] == "drafted", f"a story not drafted (answered {answered_body!r})"
