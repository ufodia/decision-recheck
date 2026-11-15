"""Reproducible fictional A/B/C and clean-control cases; no model required."""
from __future__ import annotations
import copy
from pathlib import Path
from .engine import run_case
from .storage import write_json

def example_brief(snapshot="A"):
    changed=snapshot in ("B","C")
    corrected=snapshot=="C"
    return {"schema_version":"1.0","case_id":"synthetic-saas","title":"The CSV export promise","product":"Fictional Fieldnote SaaS","scope":{"plan":"Starter","locale":"en-US","currency":"USD","billing_period":"month","tax_basis":"exclusive"},"permissions":{"allowed_hosts":[],"allow_private_network":False,"allow_test_writes":False,"allowed_actions":["read","assert_text"]},"sources":[
      {"id":"pricing","kind":"pricing","format":"json","inline":{"plan":"Starter","price":29 if changed else 9,"pro_price":49,"features":{"csv_export":not changed},"footer":"A cosmetic footer edit." if snapshot=="footer" else "Fictional demo."},"fields":{"price":"price","csv_export":"features.csv_export"}},
      {"id":"offer","kind":"offer","format":"json","inline":{"csv_export":not corrected,"text":"CSV export available on Pro." if corrected else "Starter includes CSV export."},"fields":{"csv_export":"csv_export","text":"text"}},
      {"id":"help","kind":"help","format":"json","inline":{"csv_export":not corrected,"text":"Export is available on the Pro plan." if corrected else "Export from Settings on Starter."},"fields":{"csv_export":"csv_export","text":"text"}}],
      "requirements":[{"id":"budget","label":"Stay within $20 per month","source_id":"pricing","field":"price","operator":"lte","expected":20,"hard":True},{"id":"export","label":"CSV export is included in the selected plan","source_id":"pricing","field":"csv_export","operator":"eq","expected":True,"hard":True,"task_id":"attempt-export"},{"id":"help-findability","label":"Export guidance is present","source_id":"help","field":"text","operator":"contains","expected":"Export","hard":False}],
      "claims":[{"id":"offer-export","label":"Advertising agrees with plan entitlement","source_id":"offer","field":"csv_export","actual_source_id":"pricing","actual_field":"csv_export"},{"id":"help-export","label":"Help answer agrees with plan entitlement","source_id":"help","field":"csv_export","actual_source_id":"pricing","actual_field":"csv_export"}],
      "tasks":[{"id":"understand-plan","title":"Read the selected plan","method":"fixture","check":"plan","source_id":"pricing","depends_on":["pricing"],"dependencies_complete":True},{"id":"attempt-export","title":"Attempt CSV export","method":"fixture","check":"export","source_id":"pricing","depends_on":["pricing"],"dependencies_complete":True},{"id":"find-help","title":"Find export guidance","method":"fixture","check":"help","source_id":"help","depends_on":["help"],"dependencies_complete":True}]}

def build_demo(output:Path)->dict:
    output=Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Demo output must be empty; preserve prior results.")
    output.mkdir(parents=True,exist_ok=True)
    snapshots=[]
    descriptions={"A":("Original offer","$9 Starter includes CSV export; offer and help agree."),"B":("Changed product, stale copy","Starter is $29 and export requires $49 Pro; old promises remain."),"C":("Corrected copy, unchanged buyer failure","Offer and help are corrected. The $20 buyer constraint is still unmet."),"footer":("Clean cosmetic control","Only a footer changed; selected evidence remains equivalent.")}
    for key in ("A","B","C","footer"):
        baseline=output/("B" if key=="C" else "A") if key!="A" else None
        bundle=run_case(example_brief(key),output/key,baseline=baseline)
        label,description=descriptions[key]
        snapshots.append({"id":key,"label":label,"description":description,"bundle":bundle})
        write_json(output/f"brief-{key}.json",example_brief(key))
    summary={"schema_version":"1.0","fictional":True,"model_free":True,"snapshots":snapshots}
    write_json(output/"demo-summary.json",summary)
    links="".join(f'<li><a href="{s["id"]}/report-owner.html">{s["id"]} — {s["label"]}</a>: {s["description"]}</li>' for s in snapshots)
    (output/"index.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Decision Recheck fixture</title><style>body{max-width:900px;margin:50px auto;padding:24px;background:#f7f4ea;color:#173e34;font:18px/1.7 system-ui}h1{font:54px Georgia}a{color:#215c4d}li{margin:20px 0}</style><h1>One product change.<br>Three decisions to revisit.</h1><p>Fictional, deterministic, model-free fixture. Inspect the real generated bundles and artifacts.</p><ol>'+links+'</ol><p><a href="demo-summary.json">Complete JSON demonstration</a> · <a href="https://buymeacoffee.com/ufodia">Support ufodia</a></p></html>',encoding="utf-8")
    return summary
