from __future__ import annotations

import tesser.srv as ts


class UsageError(ts.Rejection):
    pass


class CliRequest(ts.Request):

    def __init__(self, args: tuple[str, ...]) -> None:
        super().__init__(args=args)

    args: tuple[str, ...]

    def arg(self, index: int, name: str, usage: str) -> str:
        if index >= len(self.args) or not self.args[index]:
            raise UsageError(f"missing argument <{name}>\n{usage}")
        return self.args[index]

    def no_extra_args(self, count: int, usage: str) -> None:
        if len(self.args) > count:
            raise UsageError(f"unexpected extra arguments\n{usage}")

    def take_option(self, option: str, name: str, usage: str) -> tuple[CliRequest, tuple[str, ...]]:
        rest: list[str] = []
        values: list[str] = []
        remaining = iter(self.args)
        for arg in remaining:
            if arg != option:
                rest.append(arg)
                continue
            value = next(remaining, "")
            if not value or value.startswith("-"):
                raise UsageError(f"missing <{name}> after {option}\n{usage}")
            values.append(value)
        return CliRequest(args=tuple(rest)), tuple(values)

    def no_options(self, usage: str) -> None:
        for arg in self.args:
            if arg.startswith("-") and arg != "-":
                raise UsageError(f"unknown option {arg}\n{usage}")


class CliResponse(ts.Response):

    def __init__(self, exit_code: int, stdout: str, stderr: str) -> None:
        super().__init__(exit_code=exit_code, stdout=stdout, stderr=stderr)

    exit_code: int
    stdout: str
    stderr: str

    @classmethod
    def ok(cls, line: str) -> CliResponse:
        return cls(0, stdout=line, stderr="")
