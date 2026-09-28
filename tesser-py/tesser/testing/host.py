import os
import subprocess
import sys


class CliAnswer:

    def __init__(self, exit_code: int, stdout: str, stderr: str) -> None:
        self._exit_code = exit_code
        self._stdout = stdout
        self._stderr = stderr

    @property
    def exit_code(self) -> int:
        return self._exit_code

    @property
    def stdout(self) -> str:
        return self._stdout

    @property
    def stderr(self) -> str:
        return self._stderr

    def lines(self) -> tuple[str, ...]:
        return tuple(self._stdout.splitlines())


class Cli:

    def __init__(self, module: str, timeout: float = 120.0) -> None:
        self._module = module
        self._timeout = timeout

    def run(self, *args: str) -> CliAnswer:
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(path for path in sys.path if path)
        completed = subprocess.run(
            [sys.executable, "-m", self._module, *args],
            capture_output=True,
            text=True,
            env=env,
            timeout=self._timeout,
            check=False,
        )
        return CliAnswer(completed.returncode, completed.stdout, completed.stderr)


def served(variable: str) -> str:
    address = os.environ.get(variable)
    if not address:
        raise LookupError(f"{variable} is not set; the runner serves the host and names its address in {variable}")
    return address
