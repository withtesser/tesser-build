from __future__ import annotations

import json
import typing

STORIES: typing.Final[tuple[str, ...]] = (
    "As a developer, I want the steps fixed in advance, so that the agent follows them.",
    "As a developer, I want to stop at each checkpoint, so that I can weigh in.",
)

Scope = dict[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[dict[str, typing.Any]]]
Send = typing.Callable[[dict[str, typing.Any]], typing.Awaitable[None]]


class MessagesApi:

    def __init__(self) -> None:
        self.requests: list[dict[str, typing.Any]] = []

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return
        body = b""
        while True:
            event = await receive()
            body += event.get("body", b"")
            if not event.get("more_body"):
                break
        request = json.loads(body)
        self.requests.append(request)
        answer = json.dumps(
            {
                "id": "msg_simulated",
                "type": "message",
                "role": "assistant",
                "model": request["model"],
                "content": [{"type": "text", "text": json.dumps({"stories": list(STORIES)})}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        ).encode()
        await send(
            {"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]}
        )
        await send({"type": "http.response.body", "body": answer})
