from __future__ import annotations

import typing

import tesser.adapters as ts

import protocol
import rendering.client as client

_RENDER_USAGE: typing.Final[str] = (
    "usage: python -m srv.cli.render [--check] <composition-dir> <out-dir> [--print <rendered-path-or-pattern>]..."
)


class Handler(ts.Handler):

    def __init__(self, rendering_client: client.RenderingClient) -> None:
        self._rendering_client = rendering_client

    def render(self, cli_request: protocol.CliRequest) -> protocol.CliResponse:
        positional, printed = cli_request.take_option("--print", "rendered-path", _RENDER_USAGE)
        positional.no_options(_RENDER_USAGE)
        composition_dir = positional.arg(0, "composition-dir", _RENDER_USAGE)
        out_dir = positional.arg(1, "out-dir", _RENDER_USAGE)
        positional.no_extra_args(2, _RENDER_USAGE)
        render_composition_response = self._rendering_client.render_composition(
            client.RenderCompositionRequest(composition_dir=composition_dir, out_dir=out_dir, printed=printed)
        )
        if render_composition_response.problems:
            lines = "\n".join(f"render: {problem}" for problem in render_composition_response.problems)
            return protocol.CliResponse(1, stdout="", stderr=lines)
        return protocol.CliResponse.ok(
            "\n".join(render_composition_response.written)
            + "".join(f"\nremoved {path}" for path in render_composition_response.removed)
            + "".join(f"\nkept {path}" for path in render_composition_response.kept)
            + "".join(
                f"\n\n--- {printed_file.path}\n{printed_file.text.removesuffix('\n')}"
                for printed_file in render_composition_response.printed
            )
        )

    def check(self, cli_request: protocol.CliRequest) -> protocol.CliResponse:
        cli_request.no_options(_RENDER_USAGE)
        composition_dir = cli_request.arg(0, "composition-dir", _RENDER_USAGE)
        tree_dir = cli_request.arg(1, "tree", _RENDER_USAGE)
        cli_request.no_extra_args(2, _RENDER_USAGE)
        check_composition_response = self._rendering_client.check_composition(
            client.CheckCompositionRequest(composition_dir=composition_dir, tree_dir=tree_dir)
        )
        if check_composition_response.problems:
            lines = "\n".join(f"render: {problem}" for problem in check_composition_response.problems)
            return protocol.CliResponse(1, stdout="", stderr=lines)
        if check_composition_response.drifted:
            lines = "\n".join(f"check: {drifted}" for drifted in check_composition_response.drifted)
            return protocol.CliResponse(1, stdout="", stderr=lines)
        return protocol.CliResponse.ok(
            f"check: {check_composition_response.checked} rendered files match {composition_dir}"
        )
