from __future__ import annotations

import drafting.client as client


class TestRunRejected:

    def test_a_rejected_run_carries_its_code_and_message(self) -> None:
        run_rejected = client.RunRejected("empty_job", "a job to be done is never blank")
        assert run_rejected.code == "empty_job"
        assert run_rejected.message == "a job to be done is never blank"
        assert str(run_rejected) == "a job to be done is never blank"


class TestRunNotFound:

    def test_a_run_not_found_carries_its_message(self) -> None:
        run_not_found = client.RunNotFound("no run r1")
        assert run_not_found.message == "no run r1"
        assert str(run_not_found) == "no run r1"


class TestErrors:

    def test_the_declared_set_names_every_error_the_client_raises(self) -> None:
        raised = {name for name, value in vars(client).items() if isinstance(value, type) and issubclass(value, Exception)}
        assert {error.__name__ for error in client.ERRORS} == raised
