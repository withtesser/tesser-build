from __future__ import annotations

import pathlib

import tesser.testing as ts


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


def test_a_consistent_repo_checks_clean_and_lists_its_app_trees(tmp_path: pathlib.Path) -> None:
    _repo(tmp_path)
    check = ts.Cli("srv.cli.check").run(str(tmp_path))
    assert check.exit_code == 0, check.stderr
    assert "layout: 6 rows, 1 app trees" in check.stdout
    assert check.stderr == ""
    trees = ts.Cli("srv.cli.trees").run(str(tmp_path))
    assert trees.exit_code == 0, trees.stderr
    assert trees.stdout == "appone\n"


def test_a_drifted_repo_fails_the_check_and_names_each_problem(tmp_path: pathlib.Path) -> None:
    _repo(tmp_path)
    (tmp_path / "utils").mkdir()
    (tmp_path / "appone" / "pyproject.toml").write_text(
        '[project]\nname = "appone"\nrequires-python = ">=3.11"\n'
    )
    check = ts.Cli("srv.cli.check").run(str(tmp_path))
    assert check.exit_code == 1
    assert check.stdout == ""
    assert "directory 'utils' has no manifest.json row" in check.stderr
    assert "the Python floor is 3.12" in check.stderr
    trees = ts.Cli("srv.cli.trees").run(str(tmp_path))
    assert trees.exit_code == 1
    assert trees.stdout == ""
