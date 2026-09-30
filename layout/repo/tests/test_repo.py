from __future__ import annotations

import pathlib

import tesser.testing as ts

import repo.client as client
import repo.component as component


@ts.helper
def _repo(root: pathlib.Path) -> pathlib.Path:  # tesser:debt TB073
    (root / "scripts").mkdir()
    (root / "scripts" / "verify").write_text(
        "run_appone() {\n"
        "  tessercheck_tree . || return 1\n"
        "}\n"
        "run_tree() {\n"
        '  case "$1" in\n'
        "    appone)   run_appone ;;\n"
        "  esac\n"
        "}\n"
    )
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "test.yml").write_text(
        "jobs:\n"
        "  appone:\n"
        "    steps:\n"
        "      - name: gate\n"
        "        run: scripts/verify appone\n"
    )
    (root / "appone").mkdir()
    (root / "appone" / ".tesser-root").write_text("app\n")
    (root / "appone" / "requirements-dev.txt").write_text("pytest\n")
    (root / "appone" / "pyproject.toml").write_text(
        '[project]\nname = "appone"\nrequires-python = ">=3.12"\n'
    )
    (root / "docs").mkdir()
    (root / "examples" / "demo").mkdir(parents=True)
    (root / "manifest.json").write_text(
        '{".github": "ungated", "appone": "app", "docs": "ungated",'
        ' "examples": "ungated", "examples/demo": "ungated", "scripts": "ungated"}'
    )
    return root


class TestRepoContext:

    def test_a_consistent_repo_with_ungated_rows_checks_clean(self, tmp_path: pathlib.Path) -> None:
        check_layout_response = component.Repo(component.Config(component.Spec())).client.check_layout(client.CheckLayoutRequest(repo_root=str(_repo(tmp_path))))
        assert check_layout_response.problems == ()
        assert check_layout_response.counts == ("6", "1")

    def test_a_stale_python_floor_is_read_off_disk_and_reported(self, tmp_path: pathlib.Path) -> None:
        _repo(tmp_path)
        (tmp_path / "appone" / "pyproject.toml").write_text(
            '[project]\nname = "appone"\nrequires-python = ">=3.11"\n'
        )
        check_layout_response = component.Repo(component.Config(component.Spec())).client.check_layout(client.CheckLayoutRequest(repo_root=str(tmp_path)))
        assert any("the Python floor is 3.12" in p for p in check_layout_response.problems), check_layout_response.problems
