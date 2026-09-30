from __future__ import annotations

import uuid

import tests.support as support


def test_report_lists_each_added_link_with_its_verdict(host: str) -> None:
    status, created = support.call_host(host, "POST", "/campaigns", {"budget": {"amount": "100.00", "currency": "USD"}})
    assert status == 201
    slugs = {f"a-{uuid.uuid4().hex[:8]}", f"b-{uuid.uuid4().hex[:8]}"}
    for slug in slugs:
        status, _ = support.call_host(
            host, "POST", "/links", {"campaign_id": created["campaign_id"], "slug": slug, "target_url": f"https://ok.example/{slug}"}
        )
        assert status == 200
    status, report = support.call_host(host, "GET", "/reports/links-by-verdict")
    assert status == 200
    links = report["links"]
    assert isinstance(links, list)
    rows = [row for row in links if row["slug"] in slugs]
    assert {row["slug"] for row in rows} == slugs
    assert all(row["decision"] == "allowed" and row["reason"] == "ok" for row in rows)


def test_blocked_destination_never_becomes_a_link(host: str) -> None:
    status, created = support.call_host(host, "POST", "/campaigns", {"budget": {"amount": "100.00", "currency": "USD"}})
    assert status == 201
    slug = f"bad-{uuid.uuid4().hex[:8]}"
    status, problem = support.call_host(
        host, "POST", "/links", {"campaign_id": created["campaign_id"], "slug": slug, "target_url": "http://ok.example/a"}
    )
    assert status == 409
    assert problem["type"] == "/problems/target_blocked"
    status, report = support.call_host(host, "GET", "/reports/links-by-verdict")
    assert status == 200
    links = report["links"]
    assert isinstance(links, list)
    assert [row for row in links if row["slug"] == slug] == []
