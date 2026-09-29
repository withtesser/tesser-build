from __future__ import annotations

import typing

import tesser.adapters as ts

import protocol
import trees.client as client

_GENERATE_USAGE: typing.Final[str] = (
    "usage: python -m srv.cli.generate <spec.toml> <out-dir> [--print <path>]..."
)


class Handler(ts.Handler):

    def __init__(self, trees_client: client.TreesClient) -> None:
        self._trees_client = trees_client

    def generate(self, cli_request: protocol.CliRequest) -> protocol.CliResponse:
        positional, printed = cli_request.take_option("--print", "path", _GENERATE_USAGE)
        positional.no_options(_GENERATE_USAGE)
        spec_path = positional.arg(0, "spec.toml", _GENERATE_USAGE)
        out_dir = positional.arg(1, "out-dir", _GENERATE_USAGE)
        positional.no_extra_args(2, _GENERATE_USAGE)
        generate_tree_response = self._trees_client.generate_tree(
            client.GenerateTreeRequest(spec_path=spec_path, out_dir=out_dir, printed=printed)
        )
        if generate_tree_response.problems:
            lines = "\n".join(f"generate: {problem}" for problem in generate_tree_response.problems)
            return protocol.CliResponse(1, stdout="", stderr=lines)
        return protocol.CliResponse.ok(
            "\n".join(generate_tree_response.paths)
            + "".join(
                f"\n\n--- {printed_file.path}\n{printed_file.text.removesuffix('\n')}"
                for printed_file in generate_tree_response.printed
            )
        )
