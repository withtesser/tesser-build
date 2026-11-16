# tesser-build

A Python toolkit that helps your coding agents build applications in one consistent structure, and checks that every file kept to it.

- **The agent skill** teaches your agent where each piece of code goes and how each kind of class is built.
- **The analyzer** (`tessercheck`) reads the code and reports every place it breaks one of 400 rules. It runs in CI and, through a Claude Code hook, after each file your agent writes.
- **The generator** writes a starting app from a short spec file, already passing every rule.
- **The base classes** (`tesser`) are how a class says what it is, so the analyzer knows what to hold it to.

This is early work.

## Quickstart

You need Python 3.12 or later. Clone the repo, and next to it make a folder for a new app:

```
git clone https://github.com/withtesser/tesser-build
mkdir -p myapp/kernel
echo app > myapp/.tesser-root
```

The `.tesser-root` file marks the folder as an app to check. `kernel/` is where values shared across an app live.

Write a class the usual way. Save this as `myapp/kernel/email_address.py`:

```python
class EmailAddress:

    def __init__(self, value: str) -> None:
        self.value = value
```

Check it:

```
cd tesser-build/tessercheck-py
PYTHONPATH=.:../tesser-py python3 -m srv.cli.main ../../myapp
```

The analyzer exits with code 1 and prints three findings. This is the first:

```
kernel/email_address.py:1: TB052 kernel.email_address.EmailAddress declares no ts.* base; every kernel class declares its block
```

It says the class doesn't declare what it is. The other two say the file doesn't import the base classes and has no test beside it. (Python may also print a `RuntimeWarning` about `srv.cli.main`. It is harmless.)

Now write it as a value object, which is a value that checks itself and has no identity of its own:

```python
import tesser.domain as ts
import tesser.errors as errors


class EmailAddress(ts.ValueObject):

    def __init__(self, value: str) -> None:
        if "@" not in value:
            raise errors.invalid("no_at_sign", "an email address has an @")
        object.__setattr__(self, "_value", value)

    _value: str
```

And give it a test beside it, `myapp/kernel/test_email_address.py`:

```python
import pytest

import kernel.email_address as email_address
import tesser.errors as errors


def test_an_email_address_needs_an_at_sign() -> None:
    with pytest.raises(errors.DomainError):
        email_address.EmailAddress("nobody")


def test_equal_values_are_equal() -> None:
    assert email_address.EmailAddress("a@b.co") == email_address.EmailAddress("a@b.co")
```

Check it again. This time the analyzer prints no findings and exits with code 0.

The class now says what it is, and the base class gives it the rest: any `EmailAddress` that exists has passed its check, it can't be changed after it is built, and two with the same value are equal.

**Want to see a whole app?** [`examples/python-app`](examples/python-app/) is the one to read first. **Ready to use it on your own code?** See [Using it in your own project](#using-it-in-your-own-project).

## Why one structure

tesser-build's bet is that code is cheaper to change when every concept is built the same way, because a change then lands in one place instead of spreading across every call site. That only pays off if it is done every time, so the structure is written as rules a program can check.

The structure is domain-driven design: each concept gets one class that enforces its own rules, and the code is split into areas that reach each other only through a declared entry point. [`docs/start-here.md`](docs/start-here.md) explains the ideas, and [`docs/faq.md`](docs/faq.md) answers the questions that come up most.

## The analyzer

`tessercheck`, in [`tessercheck-py/`](tessercheck-py/), is what turns the structure from advice into something that is checked.

- **Reads the code without running it.** It needs only the Python standard library.
- **Passes only at zero findings.** There is no setting that turns a rule off. To excuse a finding, you mark its line, or that one file, with the rule's code.
- **Lists every rule.** All 400 are in [`tessercheck-py/RULES.md`](tessercheck-py/RULES.md).

With the Claude Code hook, the analyzer also runs each time your agent writes a Python file and hands the findings back to the agent. Setup is in [`tessercheck-cli/README.md`](tessercheck-cli/README.md).

## The agent skill

[`skills/tesser-build/`](skills/tesser-build/) is what your agent reads while it works. `SKILL.md` sends each task to the guide it needs, out of 21: one for each kind of class, and others for testing, serialization, and where code goes. The agent reads only the guides its task calls for. You copy the folder into your own repo to use it.

## The generator

[`generator/`](generator/) writes a starting app from a spec file, so nobody types the structure by hand:

```
cd generator
PYTHONPATH=.:../tesser-py python3 -m srv.cli.generate specs/shop.toml /path/to/out
```

The app it writes has one bounded context that saves and loads one kind of record, with the save running as a Restate workflow. It comes with a test beside every module and an acceptance test for the whole app. It passes the analyzer with zero findings, `mypy --strict`, and its own tests. [`generator/README.md`](generator/README.md) describes the spec file.

## The examples

[`examples/`](examples/) holds nine small apps, each kept at zero findings by CI. Start with `python-app`, which has two areas and one call between them. The others each show one thing: `minimal`, `durable-execution`, `asyncpg`, `voice`, `ports`, `llmport`, `serdepy`, and `errorspy`.

## Using it in your own project

1. **Read the docs.** Start with [`docs/start-here.md`](docs/start-here.md).
2. **Give your agent the skill.** Copy [`skills/tesser-build/`](skills/tesser-build/) into your repo.
3. **Run the analyzer in CI.** Put a `.tesser-root` file at the top of your app's folder, as in the Quickstart, and point the analyzer at that folder.

[`tessercheck-cli/README.md`](tessercheck-cli/README.md) has the one command that installs the packages from git.

## Development

```
python3 -m venv .venv && source .venv/bin/activate
scripts/install-dev              # installs what every app directory needs
scripts/verify                   # runs every check, the same way CI does
scripts/verify tessercheck-py    # or only the directories you touched
```

Each app directory listed in `manifest.json` has its own checks: the analyzer at zero findings, `mypy --strict`, and `pytest`, and some add more.

- **Some tests need Docker.** `minimal`, `durable-execution`, `voice`, `asyncpg`, `generator`, and `story-drafting` test against a real Restate engine, Postgres, or both. The tests start those as containers themselves, so Docker running is the only thing you need.
- **`specs-app` needs a browser.** Run `python -m playwright install chromium` once.
- **The `tesser-py` checks are slow.** They include mutation testing with mutmut, pinned to `3.7.0`.
- **`scripts/verify-packaging`** builds the three packages, installs them into a clean virtualenv, and runs the installed commands.

A new top-level directory or a new example needs a row in `manifest.json`, and the check in [`layout/`](layout/) fails without one. If you change a convention, change every place it is written down in the same commit. [`docs/skill-authoring.md`](docs/skill-authoring.md) has the rules for that, and [`CLAUDE.md`](CLAUDE.md) has guidance for agents working here.

The remaining directories: [`story-drafting/`](story-drafting/) and [`scripts/baseline/`](scripts/baseline/) are an experiment, a small app that agents have built from written requirements with and without these tools, and the record of every run.

## License

MIT. See [LICENSE](LICENSE).
