"""Fixed allowlisted browser actions in independent clean contexts."""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
from .policy import Budget,PolicyError,check_action,check_url,browser_resolver_rules
from .storage import artifact,now

def _launch(playwright, *, timeout_ms=30000, permissions=None):
    # A browser installation is an explicit setup prerequisite, never an implicit download.
    channel=os.environ.get("DRC_BROWSER_CHANNEL","chromium")
    if channel not in ("chromium","chrome","msedge"):
        raise PolicyError("DRC_BROWSER_CHANNEL must be chromium, chrome or msedge.")
    rules=browser_resolver_rules(permissions or {})
    return playwright.chromium.launch(channel=channel,headless=True,timeout=timeout_ms,args=["--host-resolver-rules="+rules,"--disable-quic","--no-proxy-server"])

def _route_policy(route,permissions):
    request=route.request
    try:
        check_url(request.url,permissions,resolve=False)
        if request.method not in ("GET","HEAD","OPTIONS") and permissions.get("allow_test_writes",False) is not True:
            raise PolicyError("A non-read request was blocked.")
        route.continue_()
    except (PolicyError,ValueError):
        route.abort()

def read_html_source(source,brief,budget):
    from playwright.sync_api import sync_playwright
    check_url(source["url"],brief["permissions"],resolve=False)
    with sync_playwright() as p:
        browser=_launch(p,timeout_ms=max(1,int(budget.remaining_seconds(30)*1000)),permissions=brief["permissions"])
        try:
            context=browser.new_context(service_workers="block",accept_downloads=False)
            context.route("**/*",lambda route:_route_policy(route,brief["permissions"]))
            context.route_web_socket("**/*",lambda websocket:websocket.close())
            page=context.new_page()
            page.set_default_timeout(max(1,int(budget.remaining_seconds(10)*1000)))
            budget.consume_action()
            response=page.goto(source["url"],wait_until="domcontentloaded",timeout=max(1,int(budget.remaining_seconds(15)*1000)))
            check_url(page.url,brief["permissions"],resolve=False)
            if response is None or response.status>=400:
                raise RuntimeError("The source page was not available.")
            values={}
            for key,selector in (source.get("fields") or {"text":"body"}).items():
                budget.consume_action()
                locator=page.locator(selector)
                if locator.count()!=1:
                    raise RuntimeError("A source selector must identify exactly one element.")
                text=locator.inner_text().strip()
                if not text:
                    raise RuntimeError("A source selector returned empty text.")
                values[key]=text
            raw=page.content().encode("utf-8")
            if len(raw)>budget.limits["max_response_bytes"]:
                raise RuntimeError("Source HTML exceeded the configured size.")
            return {"raw":raw,"values":values,"checked_at":now(),"observation":{"extractor":"browser-selectors-v1","fields":source.get("fields") or {"text":"body"},"scope":brief["scope"],"values":values}}
        finally:
            browser.close()

def run_task(task:dict,brief:dict,budget:Budget,output:Path)->tuple[dict,list[dict]]:
    result={"id":task["id"],"title":task.get("title",task["id"]),"method":task.get("method","browser"),"execution":"not_tested","summary":"","checked_at":now(),"evidence_ids":[],"steps":[]}
    artifacts=[]
    if task.get("method")=="fixture":
        return fixture_task(task,brief,output)
    try:
        from playwright.sync_api import sync_playwright,TimeoutError as PlaywrightTimeout
        check_url(task["url"],brief["permissions"],resolve=False)
        with sync_playwright() as p:
            browser=_launch(p,timeout_ms=max(1,int(budget.remaining_seconds(30)*1000)),permissions=brief["permissions"])
            try:
                context=browser.new_context(service_workers="block",accept_downloads=False)
                context.route("**/*",lambda route:_route_policy(route,brief["permissions"]))
                context.route_web_socket("**/*",lambda websocket:websocket.close())
                page=context.new_page()
                page.set_default_timeout(max(1,int(budget.remaining_seconds(5)*1000)))
                budget.consume_action()
                response=page.goto(task["url"],wait_until="domcontentloaded",timeout=max(1,int(budget.remaining_seconds(15)*1000)))
                check_url(page.url,brief["permissions"],resolve=False)
                if response is None or response.status>=400:
                    raise PolicyError("Task page is unavailable or access-controlled.")
                if page.locator('input[type="password"], iframe[src*="captcha"], [data-sitekey]').count():
                    raise PolicyError("Authentication or CAPTCHA requires an operator handoff.")
                assertions=0
                task_start_actions=budget.browser_actions-1
                for step in task.get("steps",[]):
                    page.set_default_timeout(max(1,int(budget.remaining_seconds(5)*1000)))
                    if budget.browser_actions-task_start_actions>=12:
                        raise RuntimeError("Per-task action cap reached.")
                    action=step.get("action")
                    check_action(action,brief["permissions"])
                    budget.consume_action()
                    locator=page.locator(step.get("selector","body"))
                    if action=="read":
                        value=locator.inner_text()
                    elif action=="assert_text":
                        expected=step.get("value","")
                        if not isinstance(expected,str) or not expected.strip():
                            raise PolicyError("assert_text needs a non-empty expected text value.")
                        assertions+=1
                        value=locator.inner_text()
                        if expected not in value:
                            result["execution"]="failed"
                            result["summary"]="The declared text assertion did not match in this test attempt."
                            result["steps"].append({"action":action,"selector":step.get("selector","body"),"matched":False})
                            break
                    elif action=="click":
                        locator.click()
                        check_url(page.url,brief["permissions"],resolve=False)
                        value="Declared synthetic test click completed."
                    elif action=="fill":
                        actual_attributes=" ".join(str(locator.get_attribute(name) or "") for name in ("type","name","id","autocomplete")).lower()
                        if any(word in (step.get("selector","")+" "+actual_attributes).lower() for word in ("password","token","secret","credit","card","cc-","cvc","cvv")):
                            raise PolicyError("Credential and payment-field entry is outside scope.")
                        locator.fill(str(step.get("value","")))
                        value="Synthetic test input entered."
                    else:
                        raise PolicyError("Unsupported action; no arbitrary code is executed.")
                    result["steps"].append({"action":action,"selector":step.get("selector","body"),"result":str(value)[:1500]})
                if result["execution"]=="not_tested":
                    if assertions:
                        result["execution"]="passed"
                        result["summary"]="All declared assertions completed in this scoped attempt."
                    else:
                        result["summary"]="Read-only capture completed without a verification assertion; product behavior remains untested."
                image=page.screenshot(full_page=False,timeout=max(1,int(budget.remaining_seconds(5)*1000)))
                capture=artifact(output,"task-capture-"+task["id"],image,"png","image/png")
                artifacts.append(capture)
                result["evidence_ids"].append(capture["id"])
            finally:
                browser.close()
    except (Exception,KeyboardInterrupt) as error:
        result["execution"]="blocked" if not isinstance(error,KeyboardInterrupt) else "interrupted"
        result["summary"]=f"Task incomplete: {type(error).__name__}. No absence or success was inferred."
        result["error_type"]=type(error).__name__
    event=artifact(output,"task-events-"+task["id"],json.dumps(result,ensure_ascii=False),"json")
    artifacts.append(event)
    result["evidence_ids"].append(event["id"])
    return result,artifacts

def fixture_task(task,brief,output):
    source=next((s for s in brief["sources"] if s["id"]==task.get("source_id")),None)
    values=(source or {}).get("inline",{})
    kind=task.get("check","export")
    if kind=="plan":
        price=values.get("price") if isinstance(values,dict) else None
        allowed=True if isinstance(price,(int,float)) and not isinstance(price,bool) and math.isfinite(price) else None
        data="Selected Starter plan: $"+str(price)+" per month." if allowed else "Fixture plan price is unknown."
    elif kind=="help":
        text=values.get("text") if isinstance(values,dict) else None
        allowed=bool(text.strip()) if isinstance(text,str) else None
        data=text if isinstance(text,str) and text.strip() else "Fixture help answer is unavailable."
    else:
        features=values.get("features",{}) if isinstance(values,dict) else None
        allowed=features.get("csv_export") if isinstance(features,dict) else None
        data="name,value\nSynthetic item,1\n" if allowed is True else "CSV export requires the Pro plan." if allowed is False else "Fixture entitlement is unknown."
    execution="passed" if allowed is True else "failed" if allowed is False else "blocked"
    capture=artifact(output,"task-capture-"+task["id"],data,"csv" if kind=="export" and allowed is True else "txt","text/csv" if kind=="export" and allowed is True else "text/plain")
    return {"id":task["id"],"title":task.get("title",task["id"]),"method":"fixture_assertion","execution":execution,"summary":"Deterministic fictional "+kind+" assertion: "+data[:300],"checked_at":now(),"evidence_ids":[capture["id"]],"steps":[{"action":"fixture_"+kind,"observed":data[:500]}]},[capture]
