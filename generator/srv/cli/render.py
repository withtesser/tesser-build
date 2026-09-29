from __future__ import annotations

import sys

import tesser.srv as ts

import app
import protocol
import rendering.adapters.handlers as rendering_handlers


class RenderHost(ts.Host):

    def run(self, argv: list[str]) -> int:
        generator_app = app.load()
        handler = rendering_handlers.Handler(generator_app.rendering.client)
        try:
            cli_response = handler.render(protocol.CliRequest(args=tuple(argv)))
        except protocol.UsageError as error:
            cli_response = protocol.CliResponse(2, stdout="", stderr=str(error))
        generator_app.close()
        if cli_response.stdout:
            print(cli_response.stdout)
        if cli_response.stderr:
            print(cli_response.stderr, file=sys.stderr)
        return cli_response.exit_code


if __name__ == "__main__":
    ts.main(RenderHost().run)
