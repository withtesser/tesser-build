from __future__ import annotations

import pathlib

import rendering.client as client
import rendering.component as component


class TestConfig:

    def test_a_config_carries_the_pieces_root(self) -> None:
        config = component.Config(component.Spec(pieces_root="/pieces"))

        assert config.pieces_root == "/pieces"


class TestRendering:

    def test_the_built_client_turns_a_missing_composition_into_problems_and_writes_nothing(self, tmp_path: pathlib.Path) -> None:
        rendering = component.Rendering(component.Config(component.Spec(pieces_root=str(tmp_path / "pieces"))))

        render_composition_response = rendering.client.render_composition(
            client.RenderCompositionRequest(composition_dir=str(tmp_path / "nowhere"), out_dir=str(tmp_path / "out"), printed=())
        )
        rendering.close()

        assert render_composition_response.problems[0] == "the composition's language.toml is missing"
        assert not (tmp_path / "out").exists()
