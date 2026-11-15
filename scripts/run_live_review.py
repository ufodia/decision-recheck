"""Explicit local configuration loader for bounded live reviews; never echo secrets."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re

from decision_recheck.engine import run_case
from decision_recheck.model import ModelClient, safe_model_failure
from decision_recheck.policy import Budget


ALLOWED_SETTINGS = {
    "DRC_MODEL_BASE_URL", "DRC_MODEL_NAME", "DRC_MODEL_API_KEY",
    "DRC_MODEL_TOKEN_PARAMETER", "DRC_BROWSER_CHANNEL",
}
REQUIRED_SETTINGS = {"DRC_MODEL_BASE_URL", "DRC_MODEL_NAME", "DRC_MODEL_API_KEY"}


class ConfigurationError(ValueError):
    """A message constructed without input values or file contents."""


def load_settings(path: Path) -> dict[str, str]:
    try:
        if path.stat().st_size > 65536:
            raise ConfigurationError("Configuration file exceeds 64 KiB.")
        content = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        raise ConfigurationError("Configuration file is missing, unreadable, or not UTF-8.") from None
    settings = {}
    for number, raw in enumerate(content.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Z][A-Z0-9_]*)\s*=(.*)", line)
        if not match:
            raise ConfigurationError(f"Line {number} must use NAME=value; its contents were not logged.")
        name, value = match.groups()
        if name not in ALLOWED_SETTINGS:
            raise ConfigurationError(f"Line {number} contains an unsupported setting.")
        if name in settings:
            raise ConfigurationError(f"Line {number} duplicates a setting.")
        value = value.strip()
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ConfigurationError(f"Line {number} has an unmatched quote.")
            value = value[1:-1]
        if not value or any(c in value for c in ("\x00", "\r", "\n")):
            raise ConfigurationError(f"Line {number} has an empty or invalid value.")
        settings[name] = value
    if not REQUIRED_SETTINGS.issubset(settings):
        raise ConfigurationError("Set DRC_MODEL_BASE_URL, DRC_MODEL_NAME and DRC_MODEL_API_KEY explicitly.")
    return settings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env.live"))
    parser.add_argument("--check-config", action="store_true", help="Validate settings without a network or model call.")
    parser.add_argument("--brief", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args(argv)
    if not args.check_config and (args.brief is None or args.output is None):
        parser.error("--brief and --output are required for a live review")
    try:
        settings = load_settings(args.env_file)
        settings.setdefault("DRC_MODEL_TOKEN_PARAMETER", "max_completion_tokens")
        # Explicit file configuration wins; it is never shell-evaluated or printed.
        os.environ.update(settings)
        ModelClient(Budget(), base_url=settings["DRC_MODEL_BASE_URL"], model=settings["DRC_MODEL_NAME"],
                    api_key=settings["DRC_MODEL_API_KEY"],
                    token_parameter=settings.get("DRC_MODEL_TOKEN_PARAMETER", "max_completion_tokens"))
        if args.check_config:
            print(json.dumps({"configuration": "valid", "model_calls": 0}))
            return 0
        bundle = run_case(args.brief, args.output, baseline=args.baseline, live_model=True)
        print(json.dumps({"status": bundle["status"], "freshness": bundle["freshness"]["state"],
                          "model_calls": bundle["usage"]["model_calls"],
                          "actual_tokens": bundle["usage"]["actual_tokens"],
                          "accepted_proposals": len(bundle["agent_proposals"])}))
        return 0 if bundle["status"] == "complete" else 3
    except ConfigurationError as error:
        print(json.dumps({"status": "configuration_error", "message": str(error)}))
        return 2
    except (Exception, KeyboardInterrupt) as error:
        # Third-party exception messages can contain credentials or request bodies.
        print(json.dumps({"status": "error", **safe_model_failure(error),
                          "message": "Review did not complete. Input values and provider messages were not logged."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
