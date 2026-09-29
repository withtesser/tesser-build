from __future__ import annotations

import pathlib

import trees.client as client
import trees.component as component


class TestGeneratingTrees:

    def test_the_voice_spec_generates_the_calls_context_with_a_call_identity_repository(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        trees = component.Trees(component.Config(component.Spec(templates_root=str(tree / "templates"))))

        generate_tree_response = trees.client.generate_tree(
            client.GenerateTreeRequest(spec_path=str(tree / "specs" / "voice.toml"), out_dir=str(tmp_path))
        )
        trees.close()

        assert generate_tree_response.problems == ()
        assert (tmp_path / ".tesser-root").read_text() == "app\nskip pgdatabase\n"
        assert "class Call(ts.AggregateRoot):" in (tmp_path / "calls" / "domain" / "call.py").read_text()
        assert "class CallIdentityRepository(ts.Port, typing.Protocol):" in (
            tmp_path / "calls" / "application" / "ports" / "call_identity_repository.py"
        ).read_text()
        assert "class TestPlacingCalls:" in (tmp_path / "tests" / "test_acceptance.py").read_text()

    def test_a_spec_with_problems_writes_nothing(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        (tmp_path / "spec.toml").write_text('app_name = "voice"\ndurable_execution_engine = "temporal"\n')
        trees = component.Trees(component.Config(component.Spec(templates_root=str(tree / "templates"))))

        generate_tree_response = trees.client.generate_tree(
            client.GenerateTreeRequest(spec_path=str(tmp_path / "spec.toml"), out_dir=str(tmp_path / "out"))
        )
        trees.close()

        assert (
            "durable_execution_engine 'temporal' has no templates; the one engine is 'restate'"
            in generate_tree_response.problems
        )
        assert not (tmp_path / "out").exists()
