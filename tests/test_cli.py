"""Public CLI recovery and portable-report contracts."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest


def cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    return subprocess.run([sys.executable, "-m", "decision_recheck", *map(str, args)], cwd=cwd, env=env, text=True, encoding="utf-8", capture_output=True, timeout=35)


def test_cli_help_exposes_actual_workflows():
    result = cli("--help")
    assert result.returncode == 0, result.stderr
    for command in ("demo", "init", "run", "recheck", "report", "validate"):
        assert command in result.stdout


def test_model_free_demo_and_every_report_view_work_from_cli(tmp_path):
    output = tmp_path / "demo"
    result = cli("demo", "--output", output)
    assert result.returncode == 0, result.stderr
    bundles = sorted(output.rglob("bundle.json"))
    assert len(bundles) >= 4, "A, B, repaired C and cosmetic control must be reproducible"
    for bundle in bundles:
        checked = cli("validate", "--bundle", bundle)
        assert checked.returncode == 0, f"{bundle}: {checked.stdout}\n{checked.stderr}"
    for view in ("owner", "buyer", "marketing"):
        report = bundles[0].parent / f"qa-{view}.html"
        rendered = cli("report", "--bundle", bundles[0], "--view", view, "--output", report)
        assert rendered.returncode == 0, rendered.stderr
        html = report.read_text(encoding="utf-8")
        assert "<html" in html.lower()
        assert len(html) > 1500
        assert "evidence" in html.lower()
        assert "HISTORICAL" in html, "Stored report rendering must not imply a current-source check"


@pytest.mark.parametrize("command", ["run", "recheck"])
def test_malformed_brief_is_a_clean_cli_error(tmp_path, command):
    brief = tmp_path / "malformed.json"
    brief.write_text('{"sources":', encoding="utf-8")
    args = [command, "--brief", str(brief), "--output", str(tmp_path / "out")]
    if command == "recheck": args.extend(["--baseline", str(tmp_path / "absent")])
    result = cli(*args)
    assert result.returncode != 0
    assert "Traceback" not in result.stderr


def test_missing_bundle_is_a_clean_cli_error(tmp_path):
    result = cli("validate", "--bundle", tmp_path / "missing.json")
    assert result.returncode != 0
    assert "Traceback" not in result.stderr


def test_init_produces_parseable_brief(tmp_path):
    brief = tmp_path / "brief.json"
    result = cli("init", "--output", brief)
    assert result.returncode == 0, result.stderr
    data = json.loads(brief.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("sources")
    assert data.get("requirements")
