import os
import uuid

import pytest

import tesser.testing.host as host


def test_served_reads_the_address_the_runner_named() -> None:
    assert host.served("PATH") == os.environ["PATH"]


def test_served_refuses_a_variable_the_runner_did_not_set() -> None:
    variable = "TESSER_UNSET_" + uuid.uuid4().hex.upper()

    with pytest.raises(LookupError, match=variable):
        host.served(variable)
