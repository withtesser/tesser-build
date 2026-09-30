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
        submitted = {"role": "a developer", "i_want": "my steps fixed in advance", "so_that": "I can pick up where we were"}
        submission = urllib_request.Request(
            f"{host}/jtbds", data=json.dumps(submitted).encode(), headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib_request.urlopen(submission, timeout=30) as submitted_answer:
            jtbd_id: str | None = json.loads(submitted_answer.read())["jtbd_id"]
        assert jtbd_id is not None
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            probe = urllib_request.Request(f"{host}/jtbds/{jtbd_id}", method="GET")
            try:
                with urllib_request.urlopen(probe, timeout=30) as probed:
                    if json.loads(probed.read()).get("status") == "awaiting_story_acceptance":
                        break
            except urllib_error.HTTPError:
                pass
            time.sleep(0.2)
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
        assert answered.get("status") == "awaiting_story_acceptance", f"not awaiting story acceptance (answered {answered_body!r})"
        stories = answered.get("stories")
        assert isinstance(stories, list) and len(stories) >= 1, f"no story (answered {answered_body!r})"
        for story in stories:
            assert all(isinstance(story.get(part), str) and story[part] != "" for part in ("given", "when", "then")), f"a story lacks a given, a when, or a then (answered {answered_body!r})"
            assert story.get("state") == "drafted", f"a story is not drafted (answered {answered_body!r})"
