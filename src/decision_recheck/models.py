"""Versioned public contracts. Source text never supplies instructions."""
from __future__ import annotations
import copy
import json
import math
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
DEFAULT_LIMITS = {"max_browser_actions":36,"max_model_calls":40,"max_tokens":12000,"timeout_seconds":1200,"max_response_bytes":1000000}
class BriefError(ValueError):
    pass

def load_brief(value: dict | str | Path) -> dict:
    brief = copy.deepcopy(value) if isinstance(value, dict) else json.loads(Path(value).read_text(encoding="utf-8"))
    if not isinstance(brief, dict):
        raise BriefError("The brief must be a JSON object.")
    if brief.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
        raise BriefError("Unsupported brief schema_version.")
    brief.setdefault("schema_version", SCHEMA_VERSION)
    brief.setdefault("case_id", brief.get("id","review"))
    brief.setdefault("title", "Product decision review")
    brief.setdefault("scope", {})
    if not isinstance(brief["scope"],dict):
        raise BriefError("scope must be an object.")
    brief.setdefault("product", brief["scope"].get("product","Supplied product"))
    brief.setdefault("permissions", {})
    brief.setdefault("limits", {})
    if not isinstance(brief["limits"],dict):
        raise BriefError("limits must be an object.")
    for key in ("sources","requirements","claims","tasks"):
        brief.setdefault(key, [])
    for key, maximum in (("sources",8),("requirements",5),("claims",10),("tasks",3)):
        if not isinstance(brief[key],list) or len(brief[key])>maximum:
            raise BriefError(f"{key} must be a list with at most {maximum} records.")
    all_ids=set()
    for key in ("sources","requirements","claims","tasks"):
        for item in brief[key]:
            if not isinstance(item,dict) or not ID.fullmatch(str(item.get("id",""))):
                raise BriefError(f"Every {key} record needs a safe stable id.")
            if item["id"] in all_ids:
                raise BriefError(f"Duplicate record id: {item['id']}")
            all_ids.add(item["id"])
    source_ids={s["id"] for s in brief["sources"]}
    for source in brief["sources"]:
        if ("url" in source)==("inline" in source):
            raise BriefError(f"Source {source['id']} needs exactly one of url or inline.")
        if source.get("format","json") not in ("json","text","html"):
            raise BriefError("Source format must be json, text or html.")
        if not isinstance(source.get("fields",{}),dict):
            raise BriefError("Source fields must be an object.")
    task_ids={t["id"] for t in brief["tasks"]}
    for req in brief["requirements"]:
        if req.get("task_id") is not None and req["task_id"] not in task_ids:
            raise BriefError("Requirement references an undeclared task.")
        if req.get("source_id") not in source_ids:
            raise BriefError(f"Unknown requirement source: {req.get('source_id')}")
        if req.get("operator","eq") not in ("eq","lte","gte","contains"):
            raise BriefError("Requirement operator must be eq, lte, gte or contains.")
        if not isinstance(req.get("field"),str) or "expected" not in req:
            raise BriefError("Requirements need field and expected.")
    for claim in brief["claims"]:
        if claim.get("source_id") not in source_ids or claim.get("actual_source_id") not in source_ids:
            raise BriefError("Claims must reference two declared sources.")
        if not isinstance(claim.get("field"),str) or not isinstance(claim.get("actual_field"),str):
            raise BriefError("Claims need field and actual_field.")
    for task in brief["tasks"]:
        if not isinstance(task.get("steps",[]),list) or len(task.get("steps",[]))>12:
            raise BriefError("A task has at most twelve steps.")
        if task.get("method","browser") not in ("browser","fixture"):
            raise BriefError("Task method must be browser or fixture.")
    limits={**DEFAULT_LIMITS,**brief["limits"]}
    for key in DEFAULT_LIMITS:
        v=limits[key]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 or (key != "timeout_seconds" and not isinstance(v,int)):
            raise BriefError(f"{key} must be a non-negative number.")
    if limits["max_browser_actions"]>36 or limits["max_model_calls"]>40:
        raise BriefError("Snapshot cap: 36 browser actions and 40 model calls.")
    if limits["max_response_bytes"]>5000000:
        raise BriefError("Response size cannot exceed 5 MB.")
    brief["limits"]=limits
    permissions=brief["permissions"]
    if not isinstance(permissions,dict) or not isinstance(permissions.get("allowed_hosts",[]),list):
        raise BriefError("permissions.allowed_hosts must be a list.")
    if any(not isinstance(v,str) or not v for v in permissions.get("allowed_hosts",[])):
        raise BriefError("Allowed hosts must be non-empty strings.")
    for flag in ("allow_private_network","allow_test_writes"):
        if flag in permissions and not isinstance(permissions[flag],bool):
            raise BriefError(f"{flag} must be a boolean.")
    if not isinstance(permissions.get("allowed_actions",[]),list) or any(not isinstance(v,str) for v in permissions.get("allowed_actions",[])):
        raise BriefError("allowed_actions must be a list of strings.")
    permissions.setdefault("allowed_hosts",[])
    permissions.setdefault("allow_private_network",False)
    permissions.setdefault("allow_test_writes",False)
    permissions.setdefault("allowed_actions",["read","assert_text"])
    return brief

def resolve_field(value: Any, path: str) -> Any:
    if path in ("","$","."):
        return value
    current=value
    for part in path.split("."):
        if isinstance(current,dict):
            current=current[part]
        elif isinstance(current,list) and part.isdigit():
            current=current[int(part)]
        else:
            raise KeyError(path)
    return current

def compare(actual: Any, operator: str, expected: Any) -> bool | None:
    if actual is None:
        return None
    if operator=="eq":
        if isinstance(actual,bool)!=isinstance(expected,bool):
            return False
        return actual==expected
    if operator in ("lte","gte"):
        if isinstance(actual,bool) or isinstance(expected,bool) or not isinstance(actual,(int,float)) or not isinstance(expected,(int,float)):
            return None
        if not math.isfinite(actual) or not math.isfinite(expected):
            return None
        return actual<=expected if operator=="lte" else actual>=expected
    if operator=="contains":
        if not isinstance(actual,(str,list,dict)):
            return None
        try:
            return expected in actual
        except TypeError:
            return None
    return None
