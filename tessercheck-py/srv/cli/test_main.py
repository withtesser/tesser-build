from __future__ import annotations

import pathlib

import pytest

import app
import srv.cli as cli


def test_a_clean_tree_runs_to_exit_code_zero(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".tesser-root").write_text("app\n", encoding="utf-8")
    assert cli.MainHost().run([str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_a_finding_runs_to_exit_code_one(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.MainHost().run([str(tmp_path)]) == 1
    assert "TB044" in capsys.readouterr().out


def test_the_app_closes_idempotently(tmp_path: pathlib.Path) -> None:
    tessercheck_app = app.load()
    tessercheck_app.close()
    tessercheck_app.close()


def test_a_usage_error_becomes_exit_code_two_with_the_usage_line(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".tesser-root").write_text("app\n", encoding="utf-8")
    assert cli.MainHost().run([str(tmp_path), "surplus"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unexpected extra arguments" in captured.err
    assert "usage: python -m srv.cli.main" in captured.err


def test_the_host_never_leaks_internals_on_the_unexpected_path(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".tesser-root").write_text("app\n", encoding="utf-8")
    assert cli.MainHost().run([f"{tmp_path}/"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "trailing separator" not in captured.err
    assert captured.err == "unexpected error\n"



def test_a_fix_renames_every_misnamed_local_in_one_run_where_a_check_rewrites_nothing(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".tesser-root").write_text("app\n", encoding="utf-8")
    (tmp_path / "mod" / "domain").mkdir(parents=True)
    (tmp_path / "mod" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "mod" / "domain" / "__init__.py").write_text(
        "from mod.domain.tag import Tag as Tag\n"
        "from mod.domain.tag import TagSpec as TagSpec\n",
        encoding="utf-8",
    )
    (tmp_path / "mod" / "domain" / "tag.py").write_text(
        "import tesser.domain as ts\n"
        "class TagSpec(ts.Spec):\n"
        "    def __init__(self, text: str) -> None:\n"
        "        self.text = text\n"
        "class Tag(ts.ValueObject):\n"
        "    def __init__(self, spec: TagSpec) -> None:\n"
        "        object.__setattr__(self, '_text', spec.text)\n",
        encoding="utf-8",
    )
    sibling = tmp_path / "mod" / "domain" / "test_tag.py"
    sibling.write_text(
        "import mod.domain as domain\n"
        "class TestTag:\n"
        "    async def test_a_tag_is_built_from_its_spec(self) -> None:\n"
        "        made = domain.TagSpec('a')\n"
        "        assert domain.Tag(made) is not None\n"
        "    async def test_two_names_settle_in_turn(self) -> None:\n"
        "        first = domain.TagSpec('a')\n"
        "        tag_spec = domain.Tag(first)\n"
        "        assert tag_spec is not None\n",
        encoding="utf-8",
    )
    before = sibling.read_text(encoding="utf-8")
    assert cli.MainHost().run([str(tmp_path)]) == 1
    checked = capsys.readouterr()
    assert checked.out.count("TB085") == 3
    assert not checked.out.startswith("fixed")
    assert sibling.read_text(encoding="utf-8") == before
    assert cli.MainHost().run(["--fix", str(tmp_path)]) == 0
    fixed = capsys.readouterr()
    assert fixed.out.startswith("fixed 3 finding(s), rewriting 1 file(s)\n")
    assert "fixed: mod/domain/test_tag.py:4: TB085 " in fixed.out
    assert "remain" not in fixed.out
    assert sibling.read_text(encoding="utf-8") == (
        "import mod.domain as domain\n"
        "class TestTag:\n"
        "    async def test_a_tag_is_built_from_its_spec(self) -> None:\n"
        "        tag_spec = domain.TagSpec('a')\n"
        "        assert domain.Tag(tag_spec) is not None\n"
        "    async def test_two_names_settle_in_turn(self) -> None:\n"
        "        tag_spec = domain.TagSpec('a')\n"
        "        tag = domain.Tag(tag_spec)\n"
        "        assert tag is not None\n"
    )
    assert cli.MainHost().run([str(tmp_path)]) == 0


def test_a_fix_lists_what_it_cannot_fix_and_exits_one(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".tesser-root").write_text("app\n", encoding="utf-8")
    (tmp_path / "mod" / "domain").mkdir(parents=True)
    (tmp_path / "mod" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "mod" / "domain" / "__init__.py").write_text(
        "from mod.domain.tag import TagSpec as TagSpec\n", encoding="utf-8"
    )
    (tmp_path / "mod" / "domain" / "tag.py").write_text(
        "import tesser.domain as ts\n"
        "class TagSpec(ts.Spec):\n"
        "    def __init__(self, text: str) -> None:\n"
        "        self.text = text\n",
        encoding="utf-8",
    )
    sibling = tmp_path / "mod" / "domain" / "test_tag.py"
    sibling.write_text(
        "import mod.domain as domain\n"
        "def test_a_spec_carries_its_text() -> None:\n"
        "    made = domain.TagSpec('a')\n"
        "    assert made.text == 'a'\n"
        "def test_a_parameter_keeps_its_name(made: domain.TagSpec) -> None:\n"
        "    assert made.text == 'a'\n",
        encoding="utf-8",
    )
    assert cli.MainHost().run([str(tmp_path), "--fix"]) == 1
    captured = capsys.readouterr()
    assert captured.out.startswith("fixed 1 finding(s), rewriting 1 file(s)\n")
    assert "1 finding(s) remain:\nmod/domain/test_tag.py:5: TB085 " in captured.out
    assert "    tag_spec = domain.TagSpec('a')\n" in sibling.read_text(encoding="utf-8")
    assert "(made: domain.TagSpec)" in sibling.read_text(encoding="utf-8")
