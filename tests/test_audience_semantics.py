"""Three audience conclusions must remain distinct after copy is repaired."""
from decision_recheck.demo import build_demo, example_brief
from decision_recheck.engine import run_case


def test_copy_repair_resolves_marketing_alignment_but_preserves_buyer_failures(tmp_path):
    catalog = build_demo(tmp_path / "demo")
    snapshots = {snapshot["id"]: snapshot["bundle"] for snapshot in catalog["snapshots"]}
    expected = {"A": "meets", "B": "fails", "C": "meets", "footer": "meets"}
    for snapshot, fit in expected.items():
        marketing = [d for d in snapshots[snapshot]["decisions"] if d["audience"] == "marketing"]
        assert len(marketing) == 1
        assert marketing[0]["fit"] == fit, (snapshot, marketing[0])
    buyer = {d["requirement_id"]: d for d in snapshots["C"]["decisions"] if d["audience"] == "buyer"}
    assert buyer["budget"]["fit"] == "fails"
    assert buyer["export"]["fit"] == "fails"
    claims = [f for f in snapshots["C"]["findings"] if f["id"].startswith("finding-claim-")]
    assert len(claims) == 2
    assert all(f["support"] == "supported" for f in claims)
    assert any(task["execution"] == "failed" for task in snapshots["C"]["tasks"])

    changed = (tmp_path / "demo" / "B" / "report-marketing.html").read_text(encoding="utf-8")
    assert "If confirmed, correct offer.csv_export for the selected plan and compare it again." in changed
    buyer_report = (tmp_path / "demo" / "C" / "report-buyer.html").read_text(encoding="utf-8")
    assert "fails · proposed · Required" in buyer_report
    assert "meets · proposed · Optional" in buyer_report
    assert "Review a different plan" in buyer_report
    owner_report = (tmp_path / "demo" / "C" / "report-owner.html").read_text(encoding="utf-8")
    assert "Reproduce the material discrepancy on the selected plan" in owner_report


def test_unresolved_fields_name_what_buyer_and_marketing_need(tmp_path):
    brief = example_brief("A")
    price = brief["requirements"][0]
    price["field"] = "invoice_price"
    brief["claims"][0]["actual_field"] = "export_terms"
    root = tmp_path / "unresolved"
    bundle = run_case(brief, root)
    buyer = next(d for d in bundle["decisions"] if d.get("requirement_id") == "budget")
    assert buyer["fit"] == "inconclusive"
    assert "Obtain the selected value for pricing.invoice_price" in buyer["next_step"]
    assert "pricing.invoice_price" in (root / "report-buyer.html").read_text(encoding="utf-8")
    claim = next(f for f in bundle["findings"] if f["id"] == "finding-claim-offer-export")
    assert claim["support"] == "insufficient"
    assert claim["evidence_ids"] == ["source-offer", "source-pricing"]
    assert "Obtain pricing.export_terms" in (root / "report-marketing.html").read_text(encoding="utf-8")


def test_price_condition_and_type_mismatch_have_distinct_follow_ups(tmp_path):
    brief = example_brief("A")
    del brief["scope"]["billing_period"]
    conditional = run_case(brief, tmp_path / "conditional")
    decision = next(d for d in conditional["decisions"] if d.get("requirement_id") == "budget")
    assert decision["fit"] == "conditional"
    assert "Confirm the currency and billing period" in decision["next_step"]

    brief["sources"][0]["inline"]["price"] = "$9 per month"
    unresolved = run_case(brief, tmp_path / "unresolved")
    decision = next(d for d in unresolved["decisions"] if d.get("requirement_id") == "budget")
    assert decision["fit"] == "inconclusive"
    assert "Select a compatible value for pricing.price" in decision["next_step"]
