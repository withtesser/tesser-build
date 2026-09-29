from __future__ import annotations

import os
import pathlib
import subprocess
import sys


class TestGeneratingTrees:

    def test_every_committed_spec_generates_every_template_and_exits_zero(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[1]
        template_count = len(list((tree / "templates").rglob("*.tmpl")))
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
            name: template_count for name in answered
        }
        assert {
            name: sorted(path.relative_to(tmp_path / name).as_posix() for path in (tmp_path / name).rglob("*") if path.is_file())
            for name in answered
        } == {name: sorted(completed.stdout.splitlines()) for name, completed in answered.items()}
