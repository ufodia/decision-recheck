"""Generate the public demo from the real, model-free CLI fixture pipeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

from decision_recheck.demo import build_demo
from decision_recheck.validate import validate_bundle


def export_demo(destination: Path) -> None:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="decision-recheck-export-") as scratch:
        work = Path(scratch).resolve()
        if not work.is_relative_to(Path(tempfile.gettempdir()).resolve()):
            raise RuntimeError("Unexpected temporary workspace")
        generated = work / "demo"
        summary = build_demo(generated)
        for snapshot in summary["snapshots"]:
            key = snapshot["id"]
            if key not in {"A", "B", "C", "footer"}:
                raise RuntimeError("Unexpected public fixture")
            source = generated / key
            errors = validate_bundle(source)
            if errors:
                raise RuntimeError("Invalid generated public fixture: " + "; ".join(errors))
            target = destination / key
            target.mkdir(exist_ok=True)
            previous_manifest = target / "bundle.json"
            if previous_manifest.exists():
                previous = json.loads(previous_manifest.read_text(encoding="utf-8"))
                new_paths = {record["path"] for record in snapshot["bundle"]["artifacts"]}
                artifact_root = (target / "artifacts").resolve()
                for record in previous.get("artifacts", []):
                    old_path = record.get("path")
                    if not isinstance(old_path, str) or old_path in new_paths:
                        continue
                    old_file = (target / old_path).resolve()
                    if old_file.is_relative_to(artifact_root) and old_file.is_file():
                        old_file.unlink()
            for filename in ("bundle.json", "report-owner.html", "report-buyer.html", "report-marketing.html"):
                shutil.copy2(source / filename, target / filename)
            shutil.copytree(source / "artifacts", target / "artifacts", dirs_exist_ok=True)
        (destination / "demo.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        with ZipFile(destination / "fixture-bundles.zip", "w", compression=ZIP_DEFLATED) as archive:
            for key in ("A", "B", "C", "footer"):
                source = generated / key
                archive.write(source / "bundle.json", key + "/bundle.json")
                for file in sorted((source / "artifacts").glob("*")):
                    if file.is_file():
                        archive.write(file, key + "/artifacts/" + file.name)
        print(json.dumps({"snapshots": len(summary["snapshots"]), "model_calls": 0, "output": str(destination)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("site/data"))
    export_demo(parser.parse_args().output)
