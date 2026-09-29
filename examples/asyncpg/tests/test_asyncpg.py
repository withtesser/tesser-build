from __future__ import annotations

import uuid

import tesser.testing as ts

import protocol


class TestCliHost:

    def test_an_added_part_is_stored_and_a_second_add_of_its_name_is_refused(self) -> None:
        cli = ts.Cli("srv.cli.main")
        name = f"e2e-{uuid.uuid4().hex}"
        taken_request = protocol.CliRequest(args=(f"{name}-taken", "p"))
        held_request = protocol.CliRequest(args=(name, name))
        repeated_request = protocol.CliRequest(args=(name, "q"))
        taken = cli.run(*taken_request.args)
        held = cli.run(*held_request.args)
        repeated = cli.run(*repeated_request.args)
        assert protocol.CliResponse(
            exit_code=taken.exit_code, line=protocol.Line(text=taken.stdout.strip())
        ) == protocol.CliResponse(exit_code=0, line=protocol.Line(text=f"{name}-taken p kept"))
        assert protocol.CliResponse(
            exit_code=held.exit_code, line=protocol.Line(text=held.stdout.strip())
        ) == protocol.CliResponse(exit_code=0, line=protocol.Line(text=f"{name} {name} released"))
        assert protocol.CliResponse(
            exit_code=repeated.exit_code, line=protocol.Line(text=repeated.stdout.strip())
        ) == protocol.CliResponse(
            exit_code=1, line=protocol.Line(text=f"widget {name!r} is already stored")
        )
