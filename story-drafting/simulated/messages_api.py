from __future__ import annotations

import json

import httpx2


class MessagesApi:
    def __init__(self) -> None:
        self.received: list[dict[str, object]] = []

    def handle(self, request: httpx2.Request) -> httpx2.Response:
        sent = json.loads(request.content)
        self.received.append(sent)
        return httpx2.Response(
            200,
            json={
                "id": "msg_simulated",
                "type": "message",
                "role": "assistant",
                "model": sent["model"],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"stories": ["As a developer, I want " + sent["messages"][0]["content"]]}),
                    }
                ],
            },
        )
