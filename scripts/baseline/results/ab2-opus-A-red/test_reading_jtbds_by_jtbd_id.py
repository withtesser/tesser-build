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
        submitted = {
            "role": "a developer",
            "i_want": "my steps fixed in advance",
            "so_that": "I can pick up where we were",
        }
        submission = urllib_request.Request(
            f"{host}/jtbds", data=json.dumps(submitted).encode(), headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib_request.urlopen(submission, timeout=30) as submitted_answer:
            created = json.loads(submitted_answer.read())
        assert isinstance(created, dict)
        jtbd_id = created.get("jtbd_id")
        assert isinstance(jtbd_id, str)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            polling = urllib_request.Request(f"{host}/jtbds/{jtbd_id}", method="GET")
            try:
                with urllib_request.urlopen(polling, timeout=30) as polled:
                    current = json.loads(polled.read())
            except urllib_error.HTTPError:
                current = {}
            if isinstance(current, dict) and current.get("status") == "awaiting_story_acceptance":
                break
            time.sleep(0.25)
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
        assert isinstance(answered, dict), f"answered {answered_body!r}"
        assert answered.get("status") == "awaiting_story_acceptance", f"answered {answered_body!r}"
        stories = answered.get("stories")
        assert isinstance(stories, list) and len(stories) >= 1, f"no story: answered {answered_body!r}"
        for story in stories:
            assert isinstance(story, dict), f"answered {answered_body!r}"
            assert isinstance(story.get("given"), str), f"answered {answered_body!r}"
            assert isinstance(story.get("when"), str), f"answered {answered_body!r}"
            assert isinstance(story.get("then"), str), f"answered {answered_body!r}"
            assert story.get("state") == "drafted", f"answered {answered_body!r}"
