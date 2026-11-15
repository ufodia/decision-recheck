"""Local credential syntax failures must never print the input secret."""
from pathlib import Path
import importlib.util

import pytest

SPEC = importlib.util.spec_from_file_location("run_live_review", Path(__file__).parents[1] / "scripts" / "run_live_review.py")
live = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(live)


def settings_text(key="synthetic-test-value"):
    return "DRC_MODEL_BASE_URL=https://models.example.test/v1\nDRC_MODEL_NAME=protocol-test\nDRC_MODEL_API_KEY=" + key + "\n"


def test_bom_and_quoted_values_are_loaded_without_shell_expansion(tmp_path):
    path = tmp_path / ".env.live"
    path.write_text(settings_text("'literal-$value'"), encoding="utf-8-sig")
    assert live.load_settings(path)["DRC_MODEL_API_KEY"] == "literal-$value"


@pytest.mark.parametrize("content", [
    "synthetic-private-value\n", "UNKNOWN=synthetic-private-value\n",
    settings_text() + "DRC_MODEL_API_KEY=synthetic-private-value\n",
    settings_text("'synthetic-private-value"), settings_text(""),
])
def test_bad_configuration_never_echoes_values(tmp_path, capsys, content):
    path = tmp_path / ".env.live"
    path.write_text(content, encoding="utf-8")
    assert live.main(["--env-file", str(path), "--check-config"]) == 2
    output = capsys.readouterr()
    assert "synthetic-private-value" not in output.out + output.err
    assert "configuration_error" in output.out


def test_configuration_check_never_dispatches_model_request(tmp_path, capsys, monkeypatch):
    path = tmp_path / ".env.live"
    path.write_text(settings_text(), encoding="utf-8")
    monkeypatch.setattr(live.ModelClient, "propose", lambda *a, **k: pytest.fail("Unexpected inference"))
    for name in live.ALLOWED_SETTINGS:
        monkeypatch.delenv(name, raising=False)
    assert live.main(["--env-file", str(path), "--check-config"]) == 0
    assert '"model_calls": 0' in capsys.readouterr().out


def test_provider_exception_text_is_not_logged(tmp_path, capsys, monkeypatch):
    path = tmp_path / ".env.live"
    path.write_text(settings_text(), encoding="utf-8")
    def failed_run(*args, **kwargs):
        raise RuntimeError("synthetic-private-provider-error")
    monkeypatch.setattr(live, "run_case", failed_run)
    for name in live.ALLOWED_SETTINGS:
        monkeypatch.delenv(name, raising=False)
    assert live.main(["--env-file", str(path), "--brief", "brief.json", "--output", "unused"]) == 2
    assert "synthetic-private-provider-error" not in capsys.readouterr().out
