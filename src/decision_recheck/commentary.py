"""Model-prioritized review points whose wording and facts stay application-owned."""
from __future__ import annotations

import hashlib
import json

CONTRACT = "canonical-review-v1"
REVIEW_ROLES = ("requirements_researcher", "offer_support_analyst", "evidence_reviewer", "report_writer")
_FITS = {"meets", "fails", "conditional", "inconclusive"}
_PROPOSAL_FIELDS = {
    "role", "review", "commentary_contract", "catalog_sha256", "review_item_ids", "evidence_ids",
    "provider_endpoint", "model", "prompt_version", "token_parameter", "max_output_tokens",
    "provider_response_id", "provider_model", "provider_created", "provider_total_tokens",
}
SELECTION_ERROR_CODES = frozenset({
    "invalid_selection_shape", "duplicate_items", "unknown_item", "missing_required_items",
    "invalid_catalog_digest", "invalid_response_shape", "invalid_response_json",
})


class CanonicalSelectionError(ValueError):
    """A fixed diagnostic code that never incorporates provider response text."""
    def __init__(self, code: str):
        self.selection_code = code if isinstance(code,str) and code in SELECTION_ERROR_CODES else "invalid_selection_shape"
        super().__init__("Canonical review selection rejected: " + self.selection_code)


def catalog_for_role(bundle: dict, role: str) -> list[dict]:
    if role not in REVIEW_ROLES:
        raise ValueError("Unsupported canonical review role.")
    if role == "requirements_researcher":
        items = [{"id": "planning", "kind": "planning", "required": True,
                  "text": "Planning-stage selection only; it does not certify task completion or requirement fulfillment.",
                  "evidence_ids": []}]
        for index, source in enumerate(bundle.get("sources", [])):
            captured = source.get("status") == "captured"
            items.append({"id": f"source-{index}", "kind": "source_review", "required": False,
                          "text": f"Review selected evidence from source '{source['id']}' within the declared scope. " +
                                  ("A captured statement is not independent runtime verification." if captured else
                                   "This source was not captured; its contents remain unestablished."),
                          "evidence_ids": [source["artifact_id"]] if captured and source.get("artifact_id") else []})
        return items
    items = [{"id": "evidence-rule", "kind": "precondition", "required": True,
              "text": "Verify actual behavior before changing a documented fact. An unmet operator criterion alone does not justify rewriting documentation or establish a product defect.",
              "evidence_ids": []}]
    follow_ups = {
        "fails": ("review_unmet_criterion", "Review the unmet criterion or collect independent behavior evidence. Change a documented fact only after that evidence establishes a correction is needed."),
        "inconclusive": ("collect_scoped_evidence", "Collect the missing evidence within the declared scope before deciding. Missing selected evidence does not establish absence across the whole product or service."),
        "conditional": ("resolve_conditions", "Resolve the recorded scope or unit conditions before treating this criterion as established."),
        "meets": ("retain_scope", "Retain the evidence date and scope. Meeting this individual criterion does not establish overall product readiness."),
    }
    for index, decision in enumerate(bundle.get("decisions", [])):
        fit = decision.get("fit")
        if fit not in _FITS:
            raise ValueError("Canonical commentary requires a valid recorded decision fit.")
        references = list(decision.get("evidence_ids", []))
        items.append({"id": f"decision-{index}", "kind": "decision", "required": True,
                      "decision_id": decision["id"], "fit": fit,
                      "text": f"Recorded {decision.get('audience', 'review')} fit for '{decision.get('title', decision['id'])}': {fit}.",
                      "evidence_ids": references})
        action, text = follow_ups[fit]
        items.append({"id": f"action-{index}", "kind": "follow_up", "required": False,
                      "decision_id": decision["id"], "fit": fit, "action": action,
                      "text": text, "evidence_ids": references})
    return items


def catalog_digest(bundle: dict, role: str) -> str:
    # Bind selections to this run and evidence, including changed task text or
    # selected source values even if their high-level fit has stayed the same.
    planning = role == "requirements_researcher"
    source_artifacts = {source.get("artifact_id") for source in bundle.get("sources", [])}
    artifacts = [record for record in bundle.get("artifacts", [])
                 if not planning or record.get("id") in source_artifacts]
    binding = {"role": role, "run_id": bundle.get("run_id"), "scope": bundle.get("scope", {}),
               "sources": bundle.get("sources", []), "tasks": [] if planning else bundle.get("tasks", []),
               "artifacts": artifacts,
               "catalog": catalog_for_role(bundle, role)}
    return hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def selection_fields(ids: list[str], catalog: list[dict], digest: str) -> dict:
    """Validate a provider's ID-only answer and derive its citations locally."""
    if not isinstance(ids, list) or not 1 <= len(ids) <= 20 or any(not isinstance(v, str) for v in ids):
        raise CanonicalSelectionError("invalid_selection_shape")
    if len(set(ids)) != len(ids):
        raise CanonicalSelectionError("duplicate_items")
    lookup = {item["id"]: item for item in catalog}
    if len(lookup) != len(catalog) or any(item not in lookup for item in ids):
        raise CanonicalSelectionError("unknown_item")
    if not {item["id"] for item in catalog if item.get("required")} <= set(ids):
        raise CanonicalSelectionError("missing_required_items")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise CanonicalSelectionError("invalid_catalog_digest")
    references = list(dict.fromkeys(reference for item in ids for reference in lookup[item]["evidence_ids"]))
    return {"commentary_contract": CONTRACT, "catalog_sha256": digest,
            "review_item_ids": list(ids), "evidence_ids": references}


def resolve_selection(bundle: dict, proposal: dict) -> list[dict]:
    """Rebuild safe wording; saved/model-supplied wording is never rendered."""
    if not isinstance(proposal, dict) or proposal.get("commentary_contract") != CONTRACT:
        raise ValueError("Legacy or unsupported model commentary is not reportable.")
    if set(proposal) - _PROPOSAL_FIELDS or proposal.get("review") != "proposed":
        raise ValueError("Untrusted fields in canonical model selection.")
    role = proposal.get("role")
    catalog = catalog_for_role(bundle, role)
    expected = selection_fields(proposal.get("review_item_ids"), catalog, catalog_digest(bundle, role))
    if proposal.get("catalog_sha256") != expected["catalog_sha256"]:
        raise ValueError("Model selection does not match the current run, evidence or decisions.")
    if proposal.get("evidence_ids") != expected["evidence_ids"]:
        raise ValueError("Canonical model selection has incorrect evidence references.")
    lookup = {item["id"]: item for item in catalog}
    return [lookup[item] for item in expected["review_item_ids"]]
