from __future__ import annotations

import os
import subprocess
import sys


def test_a_domain_rejection_becomes_an_exit_code_not_a_traceback() -> None:
    captured = subprocess.run(
        [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.cli.main", "create-campaign", "-5", "USD"],
        capture_output=True, text=True, check=False,
        env={"PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry), "CAMPAIGN_STORAGE": "memory", "LINKPOLICY_STORAGE": "memory", "HTTP_HOST": "", "HTTP_PORT": "8080"},
    )
    code = captured.returncode
    assert code == 2
    assert captured.stdout == ""
    assert captured.stderr.startswith("[")


def test_a_missing_argument_is_a_usage_error() -> None:
    captured = subprocess.run(
        [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.cli.main", "create-campaign", "100.00"],
        capture_output=True, text=True, check=False,
        env={"PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry), "CAMPAIGN_STORAGE": "memory", "LINKPOLICY_STORAGE": "memory", "HTTP_HOST": "", "HTTP_PORT": "8080"},
    )
    code = captured.returncode
    assert code == 2
    assert "usage: create-campaign" in captured.stderr


def test_an_empty_argument_is_a_usage_error() -> None:
    captured = subprocess.run(
        [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.cli.main", "create-campaign", "", "USD"],
        capture_output=True, text=True, check=False,
        env={"PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry), "CAMPAIGN_STORAGE": "memory", "LINKPOLICY_STORAGE": "memory", "HTTP_HOST": "", "HTTP_PORT": "8080"},
    )
    code = captured.returncode
    assert code == 2
    assert "missing argument <budget_amount>" in captured.stderr


def test_extra_arguments_are_a_usage_error() -> None:
    captured = subprocess.run(
        [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.cli.main", "create-campaign", "100.00", "USD", "surplus"],
        capture_output=True, text=True, check=False,
        env={"PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry), "CAMPAIGN_STORAGE": "memory", "LINKPOLICY_STORAGE": "memory", "HTTP_HOST": "", "HTTP_PORT": "8080"},
    )
    code = captured.returncode
    assert code == 2
    assert "usage: create-campaign" in captured.stderr


def test_a_lookup_that_finds_nothing_exits_one() -> None:
    captured = subprocess.run(
        [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.cli.main", "add-link", "0123456789abcdef", "promo", "https://a.example/p"],
        capture_output=True, text=True, check=False,
        env={"PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry), "CAMPAIGN_STORAGE": "memory", "LINKPOLICY_STORAGE": "memory", "HTTP_HOST": "", "HTTP_PORT": "8080"},
    )
    code = captured.returncode
    assert code == 1
    assert captured.stderr.startswith("[")


def test_an_unknown_command_is_answered_with_the_banner() -> None:
    captured = subprocess.run(
        [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.cli.main", "nope"],
        capture_output=True, text=True, check=False,
        env={"PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry), "CAMPAIGN_STORAGE": "memory", "LINKPOLICY_STORAGE": "memory", "HTTP_HOST": "", "HTTP_PORT": "8080"},
    )
    code = captured.returncode
    assert code == 2
    assert "usage: python -m srv.cli.main" in captured.stderr


def test_no_command_is_answered_with_the_banner() -> None:
    captured = subprocess.run(
        [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.cli.main"],
        capture_output=True, text=True, check=False,
        env={"PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry), "CAMPAIGN_STORAGE": "memory", "LINKPOLICY_STORAGE": "memory", "HTTP_HOST": "", "HTTP_PORT": "8080"},
    )
    code = captured.returncode
    assert code == 2
    assert "usage: python -m srv.cli.main" in captured.stderr


def test_each_campaign_command_is_wired_to_its_own_handler() -> None:
    for name in ("create-campaign", "add-link", "deactivate-link"):
        captured = subprocess.run(
            [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.cli.main", name],
            capture_output=True, text=True, check=False,
            env={"PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry), "CAMPAIGN_STORAGE": "memory", "LINKPOLICY_STORAGE": "memory", "HTTP_HOST": "", "HTTP_PORT": "8080"},
        )
        assert captured.returncode == 2
        assert f"usage: {name}" in captured.stderr


def test_create_campaign_reaches_the_campaign_context() -> None:
    captured = subprocess.run(
        [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.cli.main", "create-campaign", "100.00", "USD"],
        capture_output=True, text=True, check=False,
        env={"PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry), "CAMPAIGN_STORAGE": "memory", "LINKPOLICY_STORAGE": "memory", "HTTP_HOST": "", "HTTP_PORT": "8080"},
    )
    code = captured.returncode
    assert code == 0
    assert captured.stdout.startswith("created campaign ")
    assert captured.stderr == ""
