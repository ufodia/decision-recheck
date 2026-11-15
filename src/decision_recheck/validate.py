"""Validate bundles before trusting or exporting their evidence."""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
from .storage import load_bundle
from .models import SCHEMA_VERSION
ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,199}$")

def validate_bundle(path:str|Path)->list[str]:
    errors=[]
    try:
        bundle,root=load_bundle(path)
    except (OSError,ValueError,TypeError) as error:
        return ["Bundle is unreadable or malformed: "+type(error).__name__]
    if not isinstance(bundle,dict):
        return ["Bundle must be a JSON object."]
    if bundle.get("schema_version")!=SCHEMA_VERSION:
        errors.append("Unsupported or missing schema_version.")
    for key in ("artifacts","sources","tasks","findings","decisions"):
        if not isinstance(bundle.get(key),list):
            errors.append(f"{key} must be a list.")
    for key in ("scope","usage"):
        if not isinstance(bundle.get(key,{}),dict):
            errors.append(f"{key} must be an object.")
    for key in ("changes","agent_proposals"):
        records=bundle.get(key,[])
        if not isinstance(records,list) or any(not isinstance(record,dict) for record in records):
            errors.append(f"{key} must be a list of objects.")
    if not isinstance(bundle.get("warnings",[]),list):
        errors.append("warnings must be a list.")
    if errors:
        return errors
    artifact_ids=set()
    root=root.resolve()
    for record in bundle["artifacts"]:
        if not isinstance(record,dict):
            errors.append("Malformed artifact record.")
            continue
        aid=record.get("id")
        if not isinstance(aid,str) or not ID.fullmatch(aid) or aid in artifact_ids:
            errors.append("Invalid or duplicate artifact id.")
        if isinstance(aid,str):
            artifact_ids.add(aid)
        relative=Path(str(record.get("path","")))
        try:
            target=(root/relative).resolve()
            if relative.is_absolute() or target==root or not target.is_relative_to(root):
                errors.append(f"Artifact path escapes the bundle: {aid}")
                continue
            raw=target.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=record.get("sha256"):
                errors.append(f"Artifact hash mismatch: {aid}")
            if len(raw)!=record.get("size_bytes"):
                errors.append(f"Artifact size mismatch: {aid}")
        except (OSError,ValueError):
            errors.append(f"Missing artifact: {aid}")
    all_ids=set()
    for category in ("sources","tasks","findings","decisions"):
        for record in bundle[category]:
            if not isinstance(record,dict):
                errors.append(f"Malformed {category} record.")
                continue
            rid=record.get("id")
            if not isinstance(rid,str) or not ID.fullmatch(rid) or rid in all_ids:
                errors.append(f"Invalid or duplicate record id in {category}.")
            if isinstance(rid,str):
                all_ids.add(rid)
            references=record.get("evidence_ids",[])
            if not isinstance(references,list):
                errors.append(f"Malformed evidence references: {rid}")
                continue
            if category=="sources" and record.get("artifact_id"):
                references=[*references,record["artifact_id"]]
            if not isinstance(references,list) or any(not isinstance(v,str) or v not in artifact_ids for v in references):
                errors.append(f"Unknown evidence reference: {rid}")
            if category=="findings" and (not isinstance(record.get("audiences",[]),list) or any(not isinstance(v,str) for v in record.get("audiences",[]))):
                errors.append(f"Malformed finding audiences: {rid}")
    for change in bundle.get("changes",[]):
        if not isinstance(change.get("affected_ids",[]),list) or any(not isinstance(v,str) for v in change.get("affected_ids",[])):
            errors.append("Malformed changed-dependency references.")
    for proposal in bundle.get("agent_proposals",[]):
        references=proposal.get("evidence_ids",[])
        if not isinstance(references,list) or any(not isinstance(v,str) or v not in artifact_ids for v in references):
            errors.append("Unknown agent proposal evidence reference.")
        if "commentary_contract" in proposal:
            from .commentary import resolve_selection
            try:
                resolve_selection(bundle,proposal)
            except (ValueError,TypeError,KeyError):
                errors.append("Invalid or stale canonical commentary selection.")
    for finding in bundle["findings"]:
        if not isinstance(finding,dict):
            continue
        if finding.get("severity")=="high" and not finding.get("evidence_ids"):
            errors.append("High-priority finding has no evidence.")
    for decision in bundle["decisions"]:
        if not isinstance(decision,dict):
            continue
        if decision.get("fit") not in ("meets","fails","conditional","inconclusive"):
            errors.append("Invalid decision fit.")
        if decision.get("fit") in ("meets","fails") and not decision.get("evidence_ids"):
            errors.append("A decisive fit needs evidence.")
    freshness=bundle.get("freshness")
    if not isinstance(freshness,dict):
        errors.append("freshness must be an object.")
        return errors
    objects=freshness.get("objects")
    if not isinstance(objects,dict) or not isinstance(objects.get("observations"),dict) or not isinstance(objects.get("reasoning"),dict):
        errors.append("FreshCtx objects must contain observation and reasoning mappings.")
        return errors
    observations=objects["observations"]
    nodes=objects["reasoning"]
    known=set()
    for domain_id,record in {**observations,**nodes}.items():
        if not isinstance(domain_id,str) or not isinstance(record,dict) or not isinstance(record.get("id"),str):
            errors.append("Malformed FreshCtx object.")
            continue
        if record["id"] in known:
            errors.append("Duplicate FreshCtx object id.")
        known.add(record["id"])
    for domain_id,record in observations.items():
        if not isinstance(record,dict):
            continue
        for field in ("adapter","locator","fingerprint","validator","id","observed_at"):
            if not isinstance(record.get(field),str) or not record[field]:
                errors.append("Malformed FreshCtx observation: "+str(domain_id))
        metadata=record.get("metadata")
        if record.get("adapter")!="mcp" or not isinstance(metadata,dict) or not isinstance(metadata.get("safe"),bool) or not isinstance(metadata.get("arguments"),dict) or not isinstance(metadata.get("validator_key"),str):
            errors.append("Unsupported or malformed safe-reader observation: "+str(domain_id))
    for domain_id,record in nodes.items():
        if not isinstance(record,dict):
            continue
        dependencies=record.get("dependencies")
        if not isinstance(dependencies,list) or any(not isinstance(dep,str) or dep not in known for dep in dependencies):
            errors.append("FreshCtx reasoning has an unknown dependency: "+str(domain_id))
        for field in ("kind","digest","created_at"):
            if not isinstance(record.get(field),str):
                errors.append("Malformed FreshCtx reasoning: "+str(domain_id))
        if not isinstance(record.get("metadata"),dict):
            errors.append("Malformed FreshCtx reasoning metadata.")
    for source in bundle["sources"]:
        if isinstance(source,dict) and source.get("status")=="captured":
            observation=observations.get(source.get("id"),{}) if isinstance(source.get("id"),str) else {}
            if not isinstance(observation,dict) or source.get("observation_id")!=observation.get("id"):
                errors.append("Captured source has no matching FreshCtx observation.")
    return errors
