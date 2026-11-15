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

def _evaluate(bundle,brief,session):
    sources={s["id"]:s for s in bundle["sources"]}
    decisions=[]
    findings=[]
    tasks={t["id"]:t for t in bundle["tasks"]}
    for req in brief["requirements"]:
        source=sources.get(req["source_id"])
        actual=_field(source,req["field"])
        verdict=compare(actual,req.get("operator","eq"),req["expected"])
        fit="meets" if verdict is True else "fails" if verdict is False else "inconclusive"
        evidence=[source["artifact_id"]] if source and source.get("artifact_id") else []
        related_task=tasks.get(req.get("task_id"))
        if req.get("task_id"):
            if not related_task or related_task["execution"] in ("blocked","not_tested","interrupted"):
                fit="inconclusive"
            elif related_task["execution"]=="failed":
                fit="fails"
            if related_task:
                evidence=list(dict.fromkeys(evidence+related_task.get("evidence_ids",[])))
        rid="decision-buyer-"+req["id"]
        detail=f"Observed scoped value: {actual!r}; required {req.get('operator','eq')} {req['expected']!r}." if actual is not None else "The required scoped field was not established; request an answer or a new test."
        if req.get("task_id"):
            detail+=" Linked task outcome: "+(related_task["execution"] if related_task else "not_tested")+". A blocked attempt establishes no absence."
        if req.get("operator") in ("lte","gte") and any(not brief["scope"].get(k) for k in ("currency","billing_period")):
            # Only currency/billing-sensitive price requirements require these units.
            if "price" in req["field"].lower() or "budget" in req.get("label","").lower():
                fit="conditional"
                detail+=" Currency or billing period is missing; budget fit remains conditional."
        decisions.append({"id":rid,"audience":"buyer","requirement_id":req["id"],"title":req.get("label",req["id"]),"fit":fit,"summary":detail,"evidence_ids":evidence,"review":"proposed","hard":req.get("hard",True)})
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
        findings.append({"id":cid,"title":claim.get("label",claim["id"]),"summary":f"Supplied claim field: {expected!r}. Scoped product/document field: {observed!r}." if available else "At least one side of this comparison is missing. No contradiction or success was established.","severity":"high" if matched is False else "info","support":"conflicting" if matched is False else "supported" if matched is True else "insufficient","evidence_ids":evidence,"review":"proposed","audiences":["owner","marketing"],"suggestion":"Reproduce the scoped behavior, then qualify the supplied statement to match supported facts." if matched is False else "Retain scope and evidence date; this comparison does not predict customer response."})
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
        summary="Review the linked inconsistencies and correction drafts." if fit=="fails" else "Evidence is incomplete in the declared scope." if fit=="inconclusive" else "Requirement fit depends on the stated unresolved conditions; review them before deciding." if fit=="conditional" else "The checked requirements and supplied statements agree within the declared scope. Inspect task coverage separately; this is not proof of full product behavior." if audience=="owner" else "The checked statements agree with the supplied document fields. Inspect task coverage separately; this is not proof of full product behavior."
        decisions.append({"id":rid,"audience":audience,"title":title,"fit":fit,"summary":summary,"evidence_ids":evidence,"review":"proposed"})
        deps=list(dict.fromkeys(s for c in brief["claims"] for s in (c["source_id"],c["actual_source_id"])))
        if audience=="owner":
            deps=list(dict.fromkeys(deps+[r["source_id"] for r in brief["requirements"]]))
        deps=list(dict.fromkeys(deps+["attempt:"+t["id"] for t in bundle["tasks"]]))
        session.reason(rid,deps)
    bundle["findings"]=findings
    bundle["decisions"]=decisions

def _role(bundle,role,payload,budget):
    from .model import ModelClient
    try:
        proposal=ModelClient(budget).propose(role,payload,{a["id"] for a in bundle["artifacts"]})
        bundle["agent_proposals"].append(proposal)
        bundle["stages"].append({"role":role,"status":"proposed","at":now()})
    except (Exception,KeyboardInterrupt) as error:
        bundle["warnings"].append(f"{role} incomplete: {type(error).__name__}; no proposal was fabricated.")
        bundle["stages"].append({"role":role,"status":"blocked","error_type":type(error).__name__,"at":now()})
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
    bundle={"schema_version":"1.0","run_id":str(uuid.uuid4()),"case_id":brief["case_id"],"title":brief["title"],"product":brief["product"],"created_at":now(),"mode":mode,"status":"complete","scope":brief["scope"],"sources":[],"artifacts":[],"tasks":[],"findings":[],"decisions":[],"changes":[],"warnings":[],"agent_proposals":[],"stages":[],"usage":{},"freshness":{"provider":"freshctx","state":"UNVERIFIABLE"}}
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
            _role(bundle,"requirements_researcher",{"requirements":brief["requirements"],"sources":bundle["sources"]},budget)
        for task in brief["tasks"]:
            reused=_reuse_fixture_task(task,brief,old,baseline,source_changes,output) if old else None
            result,artifacts=reused if reused else run_task(task,brief,budget,output)
            bundle["tasks"].append(result)
            session.observe_attempt(task,result,brief)
            bundle["artifacts"].extend(artifacts)
            if result["execution"] in ("blocked","not_tested","interrupted"):
                bundle["status"]="partial"
                bundle["warnings"].append(f"Task {task['id']} was not fully tested.")
            if live_model:
                _role(bundle,"task_actor",{"goal":task.get("title",task["id"]),"attempt":result},budget)
            else:
                bundle["stages"].append({"role":"task_actor","task_id":task["id"],"status":"fixture_assertion" if mode=="fixture" else "fixed_allowlisted_steps","at":now()})
        _evaluate(bundle,brief,session)
        for role in ("offer_support_analyst","evidence_reviewer","report_writer"):
            if live_model:
                _role(bundle,role,{"findings":bundle["findings"],"decisions":bundle["decisions"],"tasks":bundle["tasks"]},budget)
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
            _write_reports(output,bundle)
        allowed,state=session.gated_write(write_current)
        if not allowed:
            bundle["freshness"]=session.export(state)
            bundle["status"]="partial"
            bundle["warnings"].append("Current-status export was blocked. This is an explicitly historical or partial report; a new scoped recheck is needed.")
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
