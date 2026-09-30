# pragma: tesser-agent-owned; generated once as a skeleton, the agent owns it from here
from __future__ import annotations

import json
import urllib.error as urllib_error
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingJtbds:

    def test_s_1_a_1(self) -> None:
        host = ts.served("STORY_DRAFTING_HOST")
        request = urllib_request.Request(
            f"{host}/jtbds", data=b'{"role": "a developer", "i_want": "the steps fixed in advance", "so_that": "I can pick up where we left off"}', headers={"Content-Type": "application/json"}, method="POST"
        )

        try:
            with urllib_request.urlopen(request, timeout=30) as answer:
                status, answered_body = answer.status, answer.read()
        except urllib_error.HTTPError as error:
            status, answered_body = error.code, error.read()

        assert status == 201
        answered = json.loads(answered_body)
        assert isinstance(answered["jtbd_id"], str) and answered["jtbd_id"] != "", f"no jtbd_id (answered {answered_body!r})"
        assert answered["status"] == "drafting_stories", f"status is not drafting_stories (answered {answered_body!r})"
