import contextlib
import os
import pathlib
import selectors
import signal
import subprocess
import sys
import time
import typing

import pytest

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
for _rel in (("..",), ("..", ".."), ("..", "..", "..")):
    _candidate = os.path.abspath(os.path.join(_root, *_rel, "tesser-py"))
    if os.path.isdir(_candidate):
        sys.path.insert(0, _candidate)
        break
else:
    raise RuntimeError(f"no tesser-py at ../, ../../ or ../../../ from {_root}")

DEADLINE_SECONDS: typing.Final[float] = 30.0
BANNER: typing.Final[str] = "specs app listening on "


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--host", help="the base URL of a host already served; without it the run serves its own")


@pytest.fixture(scope="session")
def host(request: pytest.FixtureRequest) -> typing.Iterator[str]:
    address = request.config.getoption("--host")
    if address:
        yield str(address)
        return
    served = subprocess.Popen(
        [sys.executable, "-W", "ignore::RuntimeWarning", "-m", "srv.http.main"],
        cwd=pathlib.Path(__file__).resolve().parent,
        env={
            "PYTHONPATH": os.pathsep.join(entry for entry in sys.path if entry),
            "PYTHONUNBUFFERED": "1",
            "SPECIFICATION_STORAGE": "memory",
            "HTTP_HOST": "127.0.0.1",
            "HTTP_PORT": "0",
        },
        stdout=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    with watchdog(["kill", "-KILL", f"-{served.pid}"]):
        try:
            yield f"http://{announced_address(served)}"
        finally:
            os.killpg(served.pid, signal.SIGKILL)
            served.wait()
            if served.stdout is not None:
                served.stdout.close()


def announced_address(served: subprocess.Popen[str]) -> str:
    assert served.stdout is not None
    deadline = time.monotonic() + DEADLINE_SECONDS
    with selectors.DefaultSelector() as selector:
        selector.register(served.stdout, selectors.EVENT_READ)
        while time.monotonic() < deadline:
            if selector.select(timeout=0.2):
                line = served.stdout.readline()
                if line.startswith(BANNER):
                    return str(line[len(BANNER):]).strip()
                if not line:
                    pytest.fail(f"the host exited with {served.wait()} before it announced its address")
    pytest.fail(f"the host did not announce its address within {DEADLINE_SECONDS}s")


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
