# pragma: tesser-agent-owned; generated once as a skeleton, the agent owns it from here
from __future__ import annotations

import json
import time
import urllib.error as urllib_error
import urllib.request as urllib_request


class TestReadingJtbdsByJtbdId:

    def test_s_2_a_1(self, host: str) -> None:
        submitted = {"role": "a developer", "i_want": "my steps fixed in advance", "so_that": "I can step away"}
        submission = urllib_request.Request(
            f"{host}/jtbds", data=json.dumps(submitted).encode(), headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib_request.urlopen(submission, timeout=30) as submitted_answer:
            created: object = json.loads(submitted_answer.read())
        assert isinstance(created, dict) and isinstance(created.get("jtbd_id"), str), f"POST /jtbds answered {created!r}"
        jtbd_id: str | None = created["jtbd_id"]
        assert jtbd_id is not None

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            with urllib_request.urlopen(f"{host}/jtbds/{jtbd_id}", timeout=30) as polled_answer:
                polled: object = json.loads(polled_answer.read())
            if isinstance(polled, dict) and polled.get("status") == "awaiting_story_acceptance":
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
        answered: object = json.loads(answered_body)
        assert isinstance(answered, dict), f"answered {answered_body!r}"
        assert answered.get("status") == "awaiting_story_acceptance", f"answered {answered_body!r}"
        stories = answered.get("stories")
        assert isinstance(stories, list) and len(stories) >= 1, f"answered {answered_body!r}"
        for story in stories:
            assert isinstance(story, dict), f"answered {answered_body!r}"
            assert all(isinstance(story.get(part), str) for part in ("given", "when", "then")), f"answered {answered_body!r}"
            assert story.get("state") == "drafted", f"answered {answered_body!r}"
