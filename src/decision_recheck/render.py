"""Dependency-free, escaped, offline reports. No source-supplied HTML executes."""
from __future__ import annotations
from html import escape
from pathlib import PurePosixPath
from urllib.parse import urlsplit,quote
from .commentary import CONTRACT, resolve_selection

def esc(value):
    return escape(str(value),quote=True)
def artifact_link(record):
    path=str(record.get("path",""))
    parsed=urlsplit(path)
    parts=PurePosixPath(path.replace("\\","/")).parts
    if parsed.scheme or parsed.netloc or path.startswith(("/","\\")) or ".." in parts or ":" in path:
        return ""
    return quote(path.replace("\\","/"),safe="/")
def citations(ids):
    return " ".join('<a href="#evidence-'+esc(v)+'">'+esc(v)+'</a>' for v in ids)
def render_report(bundle:dict,view:str="owner")->str:
    if view not in ("owner","buyer","marketing"):
        raise ValueError("Report view must be owner, buyer or marketing.")
    labels={"owner":"Product owner","buyer":"Buyer / user","marketing":"Marketing / support"}
    decisions=[d for d in bundle.get("decisions",[]) if d.get("audience")==view]
    findings=[f for f in bundle.get("findings",[]) if view in f.get("audiences",[])]
    scope=" · ".join(f"{k}: {v}" for k,v in bundle.get("scope",{}).items())
    freshness=bundle.get("freshness",{})
    state=freshness.get("state","HISTORICAL")
    cards=""
    for d in decisions:
        cards+='<article><div class="tag">'+esc(d.get("fit","inconclusive"))+' · '+esc(d.get("review","proposed"))+'</div><h3>'+esc(d.get("title","Decision"))+'</h3><p>'+esc(d.get("summary",""))+'</p><p class="refs">'+citations(d.get("evidence_ids",[]))+'</p></article>'
    issues=""
    for f in findings:
        issues+='<article><div class="tag">'+esc(f.get("severity","info"))+' · '+esc(f.get("support","insufficient"))+' · '+esc(f.get("review","proposed"))+'</div><h3>'+esc(f.get("title","Finding"))+'</h3><p>'+esc(f.get("summary",""))+'</p><p><strong>Proposed next step:</strong> '+esc(f.get("suggestion","Review the scoped evidence."))+'</p><p class="refs">'+citations(f.get("evidence_ids",[]))+'</p></article>'
    evidence=""
    for a in bundle.get("artifacts",[]):
        link=artifact_link(a)
        evidence+='<tr id="evidence-'+esc(a.get("id",""))+'"><td>'+esc(a.get("id",""))+'</td><td>'+('<a href="'+esc(link)+'">Open artifact</a>' if link else 'Unsafe path omitted')+'</td><td class="hash">'+esc(a.get("sha256",""))+'</td></tr>'
    tasks=""
    for t in bundle.get("tasks",[]):
        steps=""
        for step in t.get("steps",[]):
            if isinstance(step,dict):
                steps+="<li>"+"<br>".join("<strong>"+esc(key)+":</strong> "+esc(step[key]) for key in ("action","selector","expected","result","observed","matched") if key in step)+"</li>"
        details=("<details><summary>Recorded steps</summary><p>Text assertions establish text presence in the checked target, not the truth of a page claim or untested runtime/privacy behavior.</p><ol>"+steps+"</ol></details>" if steps else "")
        tasks+='<tr><td>'+esc(t.get("title",t.get("id","")))+'</td><td>'+esc(t.get("execution","not_tested"))+'</td><td>'+esc(t.get("method",""))+'<br>'+esc(t.get("summary",""))+details+'<p class="refs">'+citations(t.get("evidence_ids",[]))+'</p></td></tr>'
    changes="".join('<tr><td>'+esc(c.get("source_id",""))+'</td><td>'+esc(c.get("kind","unverifiable"))+'</td><td>'+esc(", ".join(c.get("affected_ids",[])))+'</td></tr>' for c in bundle.get("changes",[]))
    warnings="".join("<li>"+esc(w)+"</li>" for w in bundle.get("warnings",[]))
    proposals=""
    legacy_task_narration=False
    legacy_free_prose=False
    rejected_selection=False
    for p in bundle.get("agent_proposals",[]):
        if not isinstance(p,dict):
            rejected_selection=True
            continue
        if p.get("role")=="task_actor":
            legacy_task_narration=True
            continue
        if p.get("commentary_contract") != CONTRACT:
            legacy_free_prose=True
            continue
        try:
            items=resolve_selection(bundle,p)
        except (ValueError,TypeError,KeyError):
            rejected_selection=True
            continue
        selected="".join('<li><p>'+esc(item["text"])+'</p><p class="refs">'+citations(item.get("evidence_ids",[]))+'</p></li>' for item in items)
        proposals+='<article class="ai-review"><div class="tag">'+esc(p.get("role",""))+' · selected priorities</div><ol>'+selected+'</ol></article>'
    commentary_section=("<h2>AI-selected review priorities</h2><p>The model chooses priorities. Decision outcomes and required follow-ups below come from the recorded evidence and application rules; model wording cannot replace them. Selection order is a proposal for human review.</p>"+proposals if proposals else "")
    if legacy_task_narration:
        commentary_section+="<p><strong>Legacy model task narration retained in JSON; recorded task observations are execution evidence.</strong></p>"
    if legacy_free_prose:
        commentary_section+="<p><strong>Legacy free-form model commentary is retained in JSON and excluded from this report. Use the recorded decision cards and task observations.</strong></p>"
    if rejected_selection:
        commentary_section+="<p><strong>An invalid or stale model selection was excluded. Validate the bundle and run a new scoped review.</strong></p>"
    usage=bundle.get("usage",{})
    fixture_notice=("Fictional fixture with live model proposals enabled. Its sources and deterministic assertions are fictional, not customer research or a live vendor evaluation. Model proposals do not change that evidence boundary." if bundle.get("model_mode")=="live" or usage.get("model_calls",0) or bundle.get("agent_proposals") else "Fictional, model-free fixture. It is not customer research or a live vendor evaluation.")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'"><title>"""+esc(bundle.get("title","Decision Recheck"))+" — "+esc(labels[view])+"""</title><style>
:root{color-scheme:light;--ink:#173e34;--paper:#f7f4ea;--line:#cbd1c4}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 'Segoe UI',Arial,sans-serif}main{max-width:1080px;margin:auto;padding:40px 46px 70px}header{display:flex;justify-content:space-between;border-bottom:2px solid var(--ink);gap:20px;padding-bottom:18px;font-size:13px;letter-spacing:1px}h1{font:normal 58px/1.1 Georgia,serif;margin:30px 0 18px}h2{font:normal 30px Georgia,serif;margin:36px 0 18px;padding-top:20px;border-top:1px solid var(--line)}h3{font-size:20px;margin:10px 0}a{color:#215c4d;text-underline-offset:3px}a:focus-visible{outline:3px solid #8c402a;outline-offset:3px}.status{background:var(--ink);color:var(--paper);padding:23px;margin:24px 0}.status strong{display:block;font-size:20px}.tag{font:12px Consolas,monospace;text-transform:uppercase;letter-spacing:1px}article{padding:18px 20px;border:1px solid var(--line);margin:14px 0}.muted,.refs{font-size:14px;color:#52675e}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:12px}th{background:#e5eadc}.hash{font:11px Consolas,monospace;overflow-wrap:anywhere;max-width:280px}nav{display:flex;gap:20px;flex-wrap:wrap}footer{border-top:2px solid var(--ink);margin-top:40px;padding-top:20px;font-size:14px}@media(max-width:650px){main{padding:24px 20px}h1{font-size:42px}header{font-size:11px}}@media print{body{background:white}main{padding:0}nav{display:none}article,tr{break-inside:avoid}}
</style></head><body><main><header><strong>DECISION RECHECK / ufodia</strong><span>"""+esc(labels[view])+"""</span></header><h1>"""+esc(bundle.get("title","Decision review"))+"""</h1><p>"""+esc(bundle.get("product",""))+"""</p><p class="muted">"""+esc(scope)+"""</p><nav><a href="report-owner.html">Owner</a><a href="report-buyer.html">Buyer</a><a href="report-marketing.html">Marketing / support</a><a href="bundle.json">JSON bundle</a></nav><div class="status"><strong>"""+esc(state)+""" · """+esc(bundle.get("status","partial"))+"""</strong><span>Checked: """+esc(freshness.get("checked_at",bundle.get("created_at","")))+"""</span><p>"""+esc(freshness.get("meaning","Historical evidence only."))+"""</p></div><p class="muted">"""+(fixture_notice if bundle.get("mode")=="fixture" else "Scoped evidence review. Findings and decisions require human review; task results are observations at their recorded times.")+"""</p><h2>Decision cards</h2>"""+(cards or "<p>No accepted requirement conclusion is available for this view.</p>")+"""<h2>Findings and correction drafts</h2>"""+(issues or "<p>No conflicting supported finding was established in this scope. Missing work is listed below.</p>")+"""<h2>Task coverage</h2><div class="table-wrap"><table><thead><tr><th>Task</th><th>Execution</th><th>Method and observation</th></tr></thead><tbody>"""+(tasks or "<tr><td colspan='3'>No task was declared.</td></tr>")+"""</tbody></table></div><h2>Changed dependencies</h2><div class="table-wrap"><table><thead><tr><th>Source</th><th>Check</th><th>Prior decisions requiring review</th></tr></thead><tbody>"""+(changes or "<tr><td colspan='3'>No baseline comparison was requested.</td></tr>")+"""</tbody></table></div>"""+commentary_section+"""<h2>Coverage limits</h2><ul>"""+(warnings or "<li>No additional interruption was recorded. Scope limits still apply.</li>")+"""</ul><p class="muted">Model calls: """+esc(usage.get("model_calls",0))+""" · Browser actions: """+esc(usage.get("browser_actions",0))+""" · Monetary usage: unavailable. Artifact integrity does not establish a vendor claim's truth.</p><h2>Evidence manifest</h2><div class="table-wrap"><table><thead><tr><th>ID</th><th>Artifact</th><th>SHA-256</th></tr></thead><tbody>"""+evidence+"""</tbody></table></div><footer><strong>Open source, maintained by ufodia.</strong><p><a href="https://buymeacoffee.com/ufodia" rel="noopener noreferrer">Support on Buy Me a Coffee</a> · Optional support funds reproducible fixtures, adapters and documentation.</p><p>Captured: """+esc(bundle.get("created_at",""))+""" · Run """+esc(bundle.get("run_id",""))+"""</p></footer></main></body></html>"""
