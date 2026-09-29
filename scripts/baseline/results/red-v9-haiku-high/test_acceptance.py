from __future__ import annotations

import json
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmitJTBD:

    def test_submitted_jtbd_shows_drafting_status(self) -> None:
        submit_jtbd = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps(
                {
                    "description": "design new feature",
                    "status": "",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )

        with urllib_request.urlopen(submit_jtbd, timeout=30) as answer:
            assert answer.status == 201
            jtbd_id = json.loads(answer.read())["jtbd_id"]

        with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
            assert answer.status == 200
            jtbd = json.loads(answer.read())

        assert jtbd["status"] == "drafting"
