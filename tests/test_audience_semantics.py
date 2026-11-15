"""Three audience conclusions must remain distinct after copy is repaired."""
from decision_recheck.demo import build_demo


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
