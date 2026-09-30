from __future__ import annotations

import http.client as http_client
import json
import urllib.parse as urllib_parse

import tesser.testing as ts

import protocol as protocol


class TestAddStoryEndToEnd:

    def test_a_post_to_a_jtbds_stories_answers_the_storys_id_level_and_position(self) -> None:
        address = urllib_parse.urlsplit(ts.served("SPECS_APP_URL"))
        conn = http_client.HTTPConnection(address.hostname or "", address.port, timeout=5)
        conn.request(
            "POST",
            "/jtbd/j-root/stories",
            body=json.dumps({
                "given": "I am on the product specification page and a jtbd exists",
                "when": "I click add story on it, fill in given, when and then, and click save",
                "then": "I see the story nested under the jtbd",
            }),
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        http_response = protocol.HttpResponse(resp.status, resp.read(), dict(resp.getheaders()))
        conn.close()
        assert http_response.status_code == 201
        payload = http_response.json_body()
        assert payload["level"] == 1
        assert payload["story_id"] == f"j-root-s{payload['position']}"
