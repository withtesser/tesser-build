from __future__ import annotations

import pytest

import protocol


class TestCliRequest:

    def test_an_argument_is_read_by_its_index(self) -> None:
        cli_request = protocol.CliRequest(args=("c7",))
        assert cli_request.arg(0, "call_id", "usage: get-call <call_id>") == "c7"

    def test_a_missing_argument_is_a_usage_error(self) -> None:
        cli_request = protocol.CliRequest(args=())
        with pytest.raises(protocol.UsageError):
            cli_request.arg(0, "call_id", "usage: get-call <call_id>")
