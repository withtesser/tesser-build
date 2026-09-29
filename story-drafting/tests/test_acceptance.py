from __future__ import annotations

import json
import random
import time
import urllib.request as urllib_request

import tesser.testing as ts


class TestSubmittingJobsToBeDone:

    def test_a_submitted_jtbd_stops_at_the_pick_once_drafted(self) -> None:
        statement = random.choice(
            (
                "When I plan a trip I want an itinerary",
                "When I refactor I want a safety net",
                "When I onboard I want a checklist",
            )
        )
        submit_jtbd = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps({"statement": statement}).encode(),
            headers={"Content-Type": "application/json"},
        )

        with urllib_request.urlopen(submit_jtbd, timeout=10) as answer:
            submit_jtbd_status = answer.status
            jtbd_id = json.loads(answer.read())["jtbd_id"]
        with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=10) as answer:
            come_back_right_away_status = answer.status
            come_back_right_away = json.loads(answer.read())

        assert (submit_jtbd_status, come_back_right_away_status) == (201, 200)
        assert (come_back_right_away["jtbd_id"], come_back_right_away["statement"]) == (jtbd_id, statement)
        assert come_back_right_away["step"] in ("drafting", "pick")

        deadline = time.monotonic() + 20
        come_back_once_drafted = come_back_right_away
        while come_back_once_drafted["step"] != "pick" and time.monotonic() < deadline:
            time.sleep(0.5)
            with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=10) as answer:
                come_back_once_drafted = json.loads(answer.read())

        assert (
            come_back_once_drafted["step"],
            come_back_once_drafted["draft_count"] >= 1,
            come_back_once_drafted["picked_draft"],
        ) == ("pick", True, "")
