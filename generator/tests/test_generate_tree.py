from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import tomllib


class TestGeneratingTrees:

    def test_every_committed_spec_generates_every_template_its_guards_open_and_exits_zero(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[1]
        guards = {
            template.relative_to(tree / "templates").as_posix(): frozenset(
                re.findall(r"\{\{#([a-z_]+)\}\}", template.relative_to(tree / "templates").as_posix())
            )
            for template in (tree / "templates").rglob("*.tmpl")
        }
        opened = {
            spec.stem: frozenset(
                (f"storage_{stated.get('storage', 'postgres')}", f"host_{stated.get('host', 'cli')}")
            )
            for spec in sorted((tree / "specs").glob("*.toml"))
            for stated in (tomllib.loads(spec.read_text()),)
        }
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}

        answered = {
            spec.stem: subprocess.run(
                [sys.executable, "-m", "srv.cli.generate", str(spec), str(tmp_path / spec.stem)],
                capture_output=True, text=True, check=False, env=env,
            )
            for spec in sorted((tree / "specs").glob("*.toml"))
        }

        assert answered
        assert {name: (completed.returncode, completed.stderr) for name, completed in answered.items()} == {
            name: (0, "") for name in answered
        }
        assert {name: len(completed.stdout.splitlines()) for name, completed in answered.items()} == {
            name: sum(1 for guarded in guards.values() if guarded <= opened[name]) for name in answered
        }
        assert frozenset().union(*guards.values()) <= frozenset().union(*opened.values())
        assert {
            name: sorted(path.relative_to(tmp_path / name).as_posix() for path in (tmp_path / name).rglob("*") if path.is_file())
            for name in answered
        } == {name: sorted(completed.stdout.splitlines()) for name, completed in answered.items()}
