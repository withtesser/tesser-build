# pragma: tesser-agent-owned; generated once as a skeleton, the agent owns it from here
from __future__ import annotations

import json
import urllib.error as urllib_error
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingJtbds:

    def test_s_1_a_1(self) -> None:
        host = ts.served("STORY_DRAFTING_HOST")
        submitted = {
            "role": "a developer",
            "i_want": "my steps fixed in advance",
            "so_that": "I can pick up where we were",
        }
        request = urllib_request.Request(
            f"{host}/jtbds", data=json.dumps(submitted).encode(), headers={"Content-Type": "application/json"}, method="POST"
        )

        try:
            with urllib_request.urlopen(request, timeout=30) as answer:
                status, answered_body = answer.status, answer.read()
        except urllib_error.HTTPError as error:
            status, answered_body = error.code, error.read()

        assert status == 201
        answered = json.loads(answered_body)
        assert isinstance(answered, dict), f"answered {answered_body!r}"
        jtbd_id = answered.get("jtbd_id")
        assert isinstance(jtbd_id, str) and jtbd_id != "", f"no jtbd_id: answered {answered_body!r}"
        assert answered.get("status") == "drafting_stories", f"answered {answered_body!r}"
