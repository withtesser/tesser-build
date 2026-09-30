from __future__ import annotations

import tests.discovery as discovery
import tests.support as support


def test_required_roles_present_per_context() -> None:
    for ctx in discovery.discovered_contexts():
        for role in ("domain", "application", "component"):
            assert (support.ROOT / ctx / role).is_dir(), f"{ctx}/{role} missing"


def test_public_interface_is_client_plus_dtos_in_the_client_package() -> None:
    assert set(discovery.discovered_contexts()) == {"campaign", "linkpolicy", "reports"}
    for ctx, name in (("campaign", "CampaignClient"), ("linkpolicy", "LinkPolicyClient"), ("reports", "ReportsClient")):
        exported = (support.ROOT / ctx / "client" / "__init__.py").read_text(encoding="utf-8")
        assert f"{name} as {name}" in exported, f"{ctx}/client does not export {name}"


def test_config_lives_in_the_component_not_on_the_public_top_level() -> None:
    for ctx in discovery.discovered_contexts():
        exported = (support.ROOT / ctx / "component" / "__init__.py").read_text(encoding="utf-8")
        assert "Config as Config" in exported, f"{ctx}/component does not export its Config"
        assert not (support.ROOT / ctx / "config.py").exists(), f"{ctx} config leaked to the public top level"
