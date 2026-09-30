import contextlib
import http.client as http_client
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time
import typing

import pytest

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
for _rel in (("..", ".."), ("..", "..", "..")):
    _candidate = os.path.abspath(os.path.join(_root, *_rel, "tesser-py"))
    if os.path.isdir(_candidate):
        sys.path.insert(0, _candidate)
        break
else:
    raise RuntimeError(f"no tesser-py at ../../ or ../../../ from {_root}")

DEADLINE_SECONDS: typing.Final[float] = 30.0


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--host", help="the base URL of a host already served; without it the run serves its own")


@pytest.fixture(scope="session")
def host(request: pytest.FixtureRequest) -> typing.Iterator[str]:
    address = request.config.getoption("--host")
    if address:
        yield str(address)
        return
    port = unused_port()
    served = subprocess.Popen(
        [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.http.main"],
        cwd=pathlib.Path(__file__).resolve().parent,
        env={
            "PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry),
            "CAMPAIGN_STORAGE": "memory",
            "LINKPOLICY_STORAGE": "memory",
            "HTTP_HOST": "127.0.0.1",
            "HTTP_PORT": str(port),
        },
        stdout=subprocess.DEVNULL,
        start_new_session=True,
    )
    with watchdog(["kill", "-KILL", f"-{served.pid}"]):
        try:
            wait_until_answering(served, port)
            yield f"http://127.0.0.1:{port}"
        finally:
            os.killpg(served.pid, signal.SIGKILL)
            served.wait()


def unused_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def wait_until_answering(served: subprocess.Popen[bytes], port: int) -> None:
    deadline = time.monotonic() + DEADLINE_SECONDS
    while time.monotonic() < deadline:
        if served.poll() is not None:
            pytest.fail(f"the host exited with {served.returncode} before it answered")
        conn = http_client.HTTPConnection("127.0.0.1", port, timeout=1)
        try:
            conn.request("GET", "/reports/links-by-verdict")
            conn.getresponse().read()
        except OSError:
            time.sleep(0.1)
        else:
            return
        finally:
            conn.close()
    pytest.fail(f"the host did not answer on 127.0.0.1:{port} within {DEADLINE_SECONDS}s")


@contextlib.contextmanager
def watchdog(command: list[str]) -> typing.Iterator[None]:
    guard = subprocess.Popen(
        ["sh", "-c", 'cat >/dev/null; exec "$@"', "watchdog", *command],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        yield
    finally:
        guard.kill()
        guard.wait()
