"""One bounded review pipeline; all model output remains a proposal."""
from __future__ import annotations
import json
import uuid
from pathlib import Path
from .models import BriefError,compare,load_brief
from .policy import Budget,BudgetExceeded
from .storage import artifact,load_bundle,now,write_json
from .freshness import FreshnessSession
from .browser import run_task
from .render import render_report
from .validate import validate_bundle

def _field(source,field):
    return source.get("values",{}).get(field) if source and source.get("status")=="captured" else None


def _buyer_result(req, scope, actual, task):
    field = f"{req['source_id']}.{req['field']}"
    operator = req.get("operator", "eq")
    expected = req["expected"]
    verdict = compare(actual, operator, expected)
    fit = "meets" if verdict is True else "fails" if verdict is False else "inconclusive"
    observed = f"Captured {actual!r} from {field}." if actual is not None else f"No value was established for {field}."
    detail = f"{observed} Declared comparison: {operator} {expected!r}."
    task_execution = task["execution"] if task else "not_tested"
    if req.get("task_id"):
        detail += f" Linked task {req['task_id']}: {task_execution}."
        if task_execution in ("blocked", "not_tested", "interrupted"):
            return "inconclusive", detail, f"Resolve the recorded task blocker and rerun {req['task_id']} for the selected plan before deciding."
        if task_execution == "failed":
            return "fails", detail, f"Inspect the recorded assertion for {req['task_id']} and verify the route on this plan before relying on it."
    if actual is None:
        return fit, detail, f"Obtain the selected value for {field} from an authoritative source for this plan."
    if verdict is None:
        return fit, detail, f"Select a compatible value for {field} and rerun the comparison."
    is_price = "price" in req["field"].lower() or "budget" in req.get("label", "").lower()
    if is_price and operator in ("lte", "gte") and any(not scope.get(key) for key in ("currency", "billing_period")):
        return "conditional", detail, f"Confirm the currency and billing period for {field} and the buyer's limit on the same basis."
    if fit == "fails":
        return fit, detail, "Treat this criterion as unmet for the checked plan. Review a different plan or confirm that the requirement can change."
    return fit, detail, None


def _evaluate(bundle,brief,session):
    sources={s["id"]:s for s in bundle["sources"]}
    decisions=[]
    findings=[]
    tasks={t["id"]:t for t in bundle["tasks"]}
    for req in brief["requirements"]:
        source=sources.get(req["source_id"])
        actual=_field(source,req["field"])
        evidence=[source["artifact_id"]] if source and source.get("artifact_id") else []
        related_task=tasks.get(req.get("task_id"))
        if related_task:
            evidence=list(dict.fromkeys(evidence+related_task.get("evidence_ids",[])))
        fit,detail,next_step=_buyer_result(req,brief["scope"],actual,related_task)
        rid="decision-buyer-"+req["id"]
        decision={"id":rid,"audience":"buyer","requirement_id":req["id"],"title":req.get("label",req["id"]),"fit":fit,"summary":detail,"evidence_ids":evidence,"review":"proposed","hard":req.get("hard",True)}
        if next_step:
            decision["next_step"]=next_step
        decisions.append(decision)
        session.reason(rid,[req["source_id"]]+(["attempt:"+req["task_id"]] if req.get("task_id") else []))
        if fit=="fails":
            findings.append({"id":"finding-"+req["id"],"title":"Requirement is not met: "+req.get("label",req["id"]),"summary":detail,"severity":"high" if req.get("hard",True) else "medium","support":"conflicting","evidence_ids":evidence,"review":"proposed","audiences":["owner","buyer"],"suggestion":"Review the plan/requirement mismatch. Keep the buyer constraint explicit; a copy change alone cannot resolve it."})
    for claim in brief["claims"]:
        advertised=sources.get(claim["source_id"])
        actual=sources.get(claim["actual_source_id"])
        expected=_field(advertised,claim["field"])
        observed=_field(actual,claim["actual_field"])
        available=expected is not None and observed is not None
        matched=compare(observed,"eq",expected) if available else None
        evidence=[s["artifact_id"] for s in (advertised,actual) if s and s.get("artifact_id")]
        evidence=list(dict.fromkeys(evidence))
        cid="finding-claim-"+claim["id"]
        claim_field=f"{claim['source_id']}.{claim['field']}"
        product_field=f"{claim['actual_source_id']}.{claim['actual_field']}"
        if available:
            summary=f"Supplied statement {claim_field}: {expected!r}. Scoped product reference {product_field}: {observed!r}."
            suggestion=(
                f"Verify the scoped behavior against {product_field}. If confirmed, correct {claim_field} for the selected plan and compare it again."
                if matched is False else
                f"Keep the statement within the plan and terms supported by {product_field}. Verify behavior before making a broader promise."
            )
        else:
            missing=" and ".join(field for field,value in ((claim_field,expected),(product_field,observed)) if value is None)
            summary=f"The comparison is unresolved. No value was established for {missing}."
            suggestion=f"Obtain {missing} for the selected plan before publishing or correcting this statement."
        findings.append({"id":cid,"title":claim.get("label",claim["id"]),"summary":summary,"severity":"high" if matched is False else "info","support":"conflicting" if matched is False else "supported" if matched is True else "insufficient","evidence_ids":evidence,"review":"proposed","audiences":["owner","marketing"],"suggestion":suggestion})
        session.reason(cid,[claim["source_id"],claim["actual_source_id"]])
    for task in bundle["tasks"]:
        if task["execution"] in ("failed","blocked","not_tested","interrupted"):
            failed=task["execution"]=="failed"
            findings.append({"id":"finding-task-"+task["id"],"title":("Declared task assertion did not match: " if failed else "Task coverage is incomplete: ")+task["title"],"summary":task["summary"],"severity":"high" if failed else "info","support":"conflicting" if failed else "insufficient","evidence_ids":task["evidence_ids"],"review":"proposed","audiences":["owner","buyer","marketing"],"suggestion":"Reproduce the linked attempt and inspect its recorded steps before changing product or copy. An incomplete attempt does not establish that a feature is absent.","reproduction_steps":task.get("steps",[]),"classification":"task_outcome","is_product_defect":False})
    for audience,title in (("owner","Readiness for the supplied user requirements"),("marketing","Supplied promise and document alignment")):
        relevant=[f for f in findings if audience in f["audiences"] and (audience!="marketing" or f["id"].startswith("finding-claim-"))]
        requirements=[d for d in decisions if d["audience"]=="buyer"] if audience=="owner" else []
        conflict=any(f["support"]=="conflicting" for f in relevant) or any(d["fit"]=="fails" for d in requirements)
        insufficient=any(f["support"]=="insufficient" for f in relevant) or any(d["fit"]=="inconclusive" for d in requirements)
        conditional=any(d["fit"]=="conditional" for d in requirements)
        evidence=list(dict.fromkeys(e for record in [*relevant,*requirements] for e in record["evidence_ids"]))
        rid="decision-"+audience+"-alignment"
        fit="fails" if conflict else "inconclusive" if insufficient or not (relevant or requirements) else "conditional" if conditional else "meets"
        if audience=="owner":
            summary={
                "fails": "Use the linked findings to distinguish unmet buyer criteria, task assertion failures, and conflicting statements. Reproduce the material discrepancy on the selected plan before changing the product or its documentation.",
                "inconclusive": "Gather the missing source or task observations before deciding which owner action is warranted.",
                "conditional": "Resolve the recorded requirement conditions before deciding whether the plan meets the supplied needs.",
                "meets": "The supplied requirements and statements agree within the declared scope. Review the task evidence for the behavior actually exercised.",
            }[fit]
        elif not relevant:
            summary="No supplied statements were included in the document comparison."
        else:
            summary={
                "fails": "Some supplied statements conflict with their scoped product references. Verify behavior and the selected plan before correcting the indicated statements.",
                "inconclusive": "No conclusive comparison covers all supplied statements. Resolve the missing source fields before relying on the claims.",
                "meets": "The selected statement and product fields agree for this plan. Any task or buyer gaps are separate from this document comparison.",
            }[fit]
        decisions.append({"id":rid,"audience":audience,"title":title,"fit":fit,"summary":summary,"evidence_ids":evidence,"review":"proposed"})
        deps=list(dict.fromkeys(s for c in brief["claims"] for s in (c["source_id"],c["actual_source_id"])))
        if audience=="owner":
            deps=list(dict.fromkeys(deps+[r["source_id"] for r in brief["requirements"]]+["attempt:"+t["id"] for t in bundle["tasks"]]))
        if deps:
            session.reason(rid,deps)
    bundle["findings"]=findings
    bundle["decisions"]=decisions

def _role(bundle,role,payload,budget):
    from .model import ModelClient,safe_model_failure
    from .commentary import catalog_for_role,catalog_digest,resolve_selection
    catalog=catalog_for_role(bundle,role)
    required=[item["id"] for item in catalog if item.get("required")]
    context={
        "case":{key:bundle[key] for key in ("case_id","title","product","scope")},
        "sources":bundle["sources"],
        "artifact_index":[{"id":a["id"],"media_type":a["media_type"]} for a in bundle["artifacts"]],
        "review_stage":{
            "phase":"before_tasks" if role=="requirements_researcher" else "after_task" if role=="task_actor" else "after_evaluation",
            "recorded_task_count":len(bundle.get("tasks",[])),
            "formal_decision_count":len(bundle.get("decisions",[])),
            "declared_claim_count":len(payload.get("declared_claims",[])),
        },
        **payload,
        "review_catalog":catalog,
        "review_catalog_digest":catalog_digest(bundle,role),
        "required_review_item_ids":required,
        "selection_response_example":{"review_item_ids":required},
    }
    try:
        proposal=ModelClient(budget).propose(role,context,{a["id"] for a in bundle["artifacts"]})
        resolve_selection(bundle,proposal)
        bundle["agent_proposals"].append(proposal)
        bundle["stages"].append({"role":role,"status":"proposed","at":now()})
    except (Exception,KeyboardInterrupt) as error:
        failure=safe_model_failure(error)
        detail=failure["category"]
        if "http_status" in failure:
            detail+="; HTTP "+str(failure["http_status"])+"; "+failure["provider_code"]
        if "selection_code" in failure:
            detail+="; "+failure["selection_code"]
        bundle["warnings"].append(f"{role} incomplete: {failure['error_type']} ({detail}); no proposal was fabricated.")
        bundle["stages"].append({"role":role,"status":"blocked","error_type":failure["error_type"],"failure":failure,"at":now()})
        bundle["status"]="partial"

def run_case(brief:dict|Path,output:Path,baseline:Path|None=None,live_model:bool=False)->dict:
    brief=load_brief(brief)
    output=Path(output)
    if output.exists() and any(output.iterdir()):
        raise BriefError("Output directory must be empty; preserve existing evidence in a new run.")
    output.mkdir(parents=True,exist_ok=True)
    old=None
    if baseline is not None:
        errors=validate_bundle(baseline)
        if errors:
            raise BriefError("Baseline failed evidence validation: "+"; ".join(errors))
        old,_=load_bundle(baseline)
        if old.get("case_id")!=brief["case_id"]:
            raise BriefError("Baseline and brief must share the same case_id.")
    budget=Budget(brief["limits"])
    mode="fixture" if all("inline" in s for s in brief["sources"]) and all(t.get("method")=="fixture" for t in brief["tasks"]) else "live"
    bundle={"schema_version":"1.0","run_id":str(uuid.uuid4()),"case_id":brief["case_id"],"title":brief["title"],"product":brief["product"],"created_at":now(),"mode":mode,"model_mode":"live" if live_model else "disabled","status":"complete","scope":brief["scope"],"sources":[],"artifacts":[],"tasks":[],"findings":[],"decisions":[],"changes":[],"warnings":[],"agent_proposals":[],"stages":[],"usage":{},"freshness":{"provider":"freshctx","state":"UNVERIFIABLE"}}
    if not brief["sources"]:
        bundle["status"]="partial"
        bundle["warnings"].append("No source was declared.")
    write_json(output/"brief.json",brief)
    with FreshnessSession(output,bundle["run_id"]) as session:
        for source in brief["sources"]:
            holder=[]
            record={"id":source["id"],"kind":source.get("kind","document"),"url":source.get("url","inline:"+source["id"]),"checked_at":now(),"status":"unverifiable","values":{}}
            try:
                token=session.observe(source,brief,budget,holder)
                captured=holder[0]
                capture=artifact(output,"source-"+source["id"],captured["raw"],"json" if source.get("format","json")=="json" else "txt","application/json" if source.get("format","json")=="json" else "text/plain")
                bundle["artifacts"].append(capture)
                record.update(status="captured",values=captured["values"],checked_at=captured["checked_at"],artifact_id=capture["id"],observation_id=token.id)
            except (Exception,KeyboardInterrupt) as error:
                record["error_type"]=type(error).__name__
                session.incomplete_nodes.append("source-"+source["id"])
                bundle["warnings"].append(f"Source {source['id']} unavailable: {type(error).__name__}.")
                bundle["status"]="partial"
            bundle["sources"].append(record)
            write_json(output/"checkpoint.json",{"stage":"collect","source_id":source["id"],"status":record["status"],"run_id":bundle["run_id"]})
        source_changes=session.source_changes(old) if old else {}
        bundle["stages"].append({"role":"requirements_researcher","status":"deterministic" if not live_model else "pending","at":now()})
        if live_model:
            _role(bundle,"requirements_researcher",{"requirements":brief["requirements"],"sources":bundle["sources"],"declared_claims":brief["claims"]},budget)
        for task in brief["tasks"]:
            reused=_reuse_fixture_task(task,brief,old,baseline,source_changes,output) if old else None
            result,artifacts=reused if reused else run_task(task,brief,budget,output)
            bundle["tasks"].append(result)
            session.observe_attempt(task,result,brief)
            bundle["artifacts"].extend(artifacts)
            if result["execution"] in ("blocked","not_tested","interrupted"):
                bundle["status"]="partial"
                bundle["warnings"].append(f"Task {task['id']} was not fully tested.")
            actor_status="reused_historical" if result.get("method")=="reused_historical" else "fixture_assertion" if task.get("method")=="fixture" else "fixed_allowlisted_steps"
            bundle["stages"].append({"role":"task_actor","task_id":task["id"],"status":actor_status,"model_used":False,"at":now()})
        _evaluate(bundle,brief,session)
        for role in ("offer_support_analyst","evidence_reviewer","report_writer"):
            if live_model:
                _role(bundle,role,{"findings":bundle["findings"],"decisions":bundle["decisions"],"tasks":bundle["tasks"],"declared_claims":brief["claims"]},budget)
            else:
                bundle["stages"].append({"role":role,"status":"deterministic","at":now()})
        if old:
            bundle["changes"]=session.check_baseline(old)
        bundle["usage"]={**budget.usage(),"attempts_executed":sum(t.get("method")!="reused_historical" for t in bundle["tasks"]),"attempts_reused":sum(t.get("method")=="reused_historical" for t in bundle["tasks"])}
        if mode=="fixture":
            bundle["warnings"].append("Fictional fixture: inline data and deterministic task assertions are not live customer or vendor evidence.")
        if any(t.get("method")=="reused_historical" for t in bundle["tasks"]):
            bundle["warnings"].append("Unaffected pure fixture attempts were reused as historical evidence with their original times. They were not freshly executed.")
        if any(s["kind"]=="alternative" for s in bundle["sources"]):
            bundle["warnings"].append("Alternative sources are documentary only; their product behavior was not browser-tested.")
        def write_current():
            bundle["freshness"]=session.export("CURRENT")
            if session.guard.result:
                bundle["freshness"]["receipts"].append({"purpose":"current_report_export",**session.guard.result.to_dict()})
            bundle["usage"]={**bundle["usage"],**budget.usage()}
            _write_reports(output,bundle)
        allowed,state=session.gated_write(write_current)
        if not allowed:
            bundle["freshness"]=session.export(state)
            bundle["status"]="partial"
            bundle["warnings"].append("Current-status export was blocked. This is an explicitly historical or partial report; a new scoped recheck is needed.")
            bundle["usage"]={**bundle["usage"],**budget.usage()}
            _write_reports(output,bundle)
    errors=validate_bundle(output)
    if errors:
        raise RuntimeError("Generated bundle failed validation: "+"; ".join(errors))
    return bundle

def _write_reports(output,bundle):
    write_json(output/"bundle.json",bundle)
    for view in ("owner","buyer","marketing"):
        (output/f"report-{view}.html").write_text(render_report(bundle,view),encoding="utf-8")
    write_json(output/"checkpoint.json",{"stage":"reported","status":bundle["status"],"run_id":bundle["run_id"]})


def _reuse_fixture_task(task,brief,old,baseline,changes,output):
    if task.get("method")!="fixture" or task.get("dependencies_complete") is not True:
        return None
    dependencies=task.get("depends_on")
    if not isinstance(dependencies,list) or not dependencies or set(dependencies)!={task.get("source_id")}:
        return None
    source=next((s for s in brief["sources"] if s["id"]==task.get("source_id")),{})
    required_path={"plan":"price","help":"text","export":"features.csv_export"}.get(task.get("check","export"))
    if "inline" not in source or required_path not in source.get("fields",{}).values() or any(changes.get(dep)!="CURRENT" for dep in dependencies):
        return None
    previous=next((t for t in old.get("tasks",[]) if t["id"]==task["id"]),None)
    old_token=old.get("freshness",{}).get("objects",{}).get("observations",{}).get("attempt:"+task["id"],{})
    previous_spec=old_token.get("metadata",{}).get("arguments",{}).get("task_spec")
    if not previous or previous["execution"]!="passed" or previous_spec!=task or old.get("scope")!=brief["scope"] or old_token.get("metadata",{}).get("arguments",{}).get("fixture_contract")!="pure-fixture-v1":
        return None
    _,root=load_bundle(baseline)
    evidence=[]
    records={a["id"]:a for a in old["artifacts"]}
    for aid in previous["evidence_ids"]:
        record=records[aid]
        raw=(root/record["path"]).read_bytes()
        extension=Path(record["path"]).suffix.lstrip(".") or "bin"
        evidence.append(artifact(output,aid,raw,extension,record["media_type"]))
    result={**previous,"method":"reused_historical","reused_from":old["run_id"],"summary":"Historical pure fixture attempt reused after equivalent dependency checks; not freshly executed. "+previous["summary"]}
    return result,evidence
