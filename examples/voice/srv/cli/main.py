from __future__ import annotations

import asyncio
import sys
import traceback
import typing

import tesser.srv as ts

import app as app
import calls.adapters.handlers as calls_handlers
import protocol as protocol

_USAGE: typing.Final[str] = "usage: place-call | get-call <call_id>"


class CliHost(ts.Host):

    def run(self, argv: list[str]) -> int:
        try:
            voice_app = app.load()
            cli_handler = calls_handlers.CliHandler(voice_app.calls.client)
            commands: dict[str, protocol.Command] = {
                "place-call": cli_handler.place_call,
                "get-call": cli_handler.get_call,
            }
            with asyncio.Runner() as runner:
                runner.run(voice_app.open())
                try:
                    if not argv or argv[0] not in commands:
                        raise protocol.UsageError(_USAGE)
                    cli_response = runner.run(commands[argv[0]](protocol.CliRequest(args=tuple(argv[1:]))))
                except protocol.UsageError as e:
                    cli_response = protocol.CliResponse(exit_code=2, line=protocol.Line(text=str(e)))
                finally:
                    runner.run(voice_app.close())
            sys.stdout.write(cli_response.line.text + "\n")
            return cli_response.exit_code
        except Exception:
            traceback.print_exc(file=sys.stderr)
            sys.stdout.write("unexpected error\n")
            return 1


if __name__ == "__main__":
    ts.main(CliHost().run)
