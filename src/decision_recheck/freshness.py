"""FreshCtx integration. This module does not implement a competing DAG."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import freshctx
from .collector import source_reader
from .storage import now

class FreshnessSession:
    def __init__(self,output:Path,run_id:str):
        self.store=freshctx.MemoryStore()
        self.guard=freshctx.guard(policy="block",store=self.store,run_id=run_id,audit_path=output/"freshctx-audit.jsonl")
        self.tokens={}
        self.nodes={}
        self.readers={}
        self.receipts=[]
        self.incomplete_nodes=[]
    def __enter__(self):
        self.guard.__enter__()
        return self
    def __exit__(self,*args):
        return self.guard.__exit__(*args)
    def observe(self,source,brief,budget,holder):
        reader=source_reader(source,brief,budget,holder)
        self.readers[source["id"]]=reader
        token=freshctx.observe("decision-recheck://source/"+source["id"],adapter="mcp",name="read_scoped_source",arguments={"fields":source.get("fields",{}),"scope":brief["scope"],"url":source.get("url","inline:"+source["id"])},reader=reader,safe=True)
        self.tokens[source["id"]]=token
        return token
    def observe_attempt(self,task,result,brief):
        selected={"execution":result["execution"],"steps":result.get("steps",[])}
        key="attempt:"+task["id"]
        token=freshctx.observe("decision-recheck://attempt/"+task["id"],adapter="mcp",name="read_recorded_attempt",arguments={"scope":brief["scope"],"task_spec":task,"fixture_contract":"pure-fixture-v1" if task.get("method")=="fixture" else "fixed-browser-steps-v1"},reader=lambda:selected,safe=True)
        self.tokens[key]=token
        return token
    def reason(self,domain_id,source_ids):
        dependencies=[self.tokens[s].id for s in source_ids if s in self.tokens]
        if not dependencies or len(dependencies)!=len(set(source_ids)):
            self.incomplete_nodes.append(domain_id)
            return None
        with freshctx.reasoning("decision-recheck",depends_on=dependencies,metadata={"domain_id":domain_id}) as node:
            pass
        self.nodes[domain_id]=node.node
        return node.node
    def source_changes(self,baseline):
        changes={}
        for domain_id,raw in baseline.get("freshness",{}).get("objects",{}).get("observations",{}).items():
            if domain_id.startswith("attempt:"):
                continue
            token=freshctx.ObservationToken(**raw)
            current=self.tokens.get(domain_id)
            if current and current.adapter==token.adapter and current.metadata.get("validator_key")==token.metadata.get("validator_key"):
                self.store.put_observation(token)
            receipt=self.guard.check(token,require_current=True).to_dict()
            changes[domain_id]=receipt["state"]
            self.receipts.append({"source_id":domain_id,"purpose":"fixture_task_selection",**receipt})
        return changes
    def check_baseline(self,baseline):
        prior=baseline.get("freshness",{}).get("objects",{})
        tokens={}
        for domain_id,raw in prior.get("observations",{}).items():
            try:
                token=freshctx.ObservationToken(**raw)
                current=self.tokens.get(domain_id)
                if current and current.adapter==token.adapter and current.metadata.get("validator_key")==token.metadata.get("validator_key"):
                    self.store.put_observation(token)
                tokens[domain_id]=token
            except (TypeError,ValueError):
                continue
        restored={}
        for domain_id,raw in prior.get("reasoning",{}).items():
            try:
                raw={**raw,"dependencies":tuple(raw["dependencies"])}
                node=freshctx.ReasoningNode(**raw)
                self.store.put_reasoning(node)
                restored[domain_id]=node
            except (TypeError,ValueError,KeyError):
                continue
        checks={}
        for domain_id,node in restored.items():
            receipt=self.guard.check(node,require_current=True).to_dict()
            checks[domain_id]=receipt
            self.receipts.append({"domain_id":domain_id,"purpose":"baseline_recheck",**receipt})
        changes=[]
        for source_id,token in tokens.items():
            receipt=self.guard.check(token,require_current=True).to_dict()
            state=receipt["state"]
            changes.append({"source_id":source_id,"kind":"unchanged" if state=="CURRENT" else "changed" if state=="STALE_SOURCE" else "unverifiable","state":state,"affected_ids":[domain_id for domain_id,node in restored.items() if state!="CURRENT" and token.id in node.dependencies and checks[domain_id]["state"]!="CURRENT"]})
            self.receipts.append({"source_id":source_id,"purpose":"baseline_source_recheck",**receipt})
        return changes
    def gated_write(self,writer):
        subjects=[node.id for node in self.nodes.values()]+["unverified:"+item for item in self.incomplete_nodes]
        if not subjects:
            return False,"UNVERIFIABLE"
        try:
            self.guard.run(writer,depends_on=subjects,boundary="current_report_export")
            if self.guard.result is not None:
                self.receipts.append({"purpose":"current_report_export",**self.guard.result.to_dict()})
            return True,"CURRENT"
        except freshctx.FreshnessBlocked as error:
            receipt=error.result.to_dict()
            self.receipts.append({"purpose":"current_report_export",**receipt})
            return False,receipt["state"]
    def export(self,state):
        return {"provider":"freshctx","version":freshctx.__version__,"state":state,"checked_at":now(),"meaning":"Selected declared source fields were revalidated. CURRENT is not truth or a fresh browser-task result.","receipts":self.receipts,"objects":{"observations":{k:asdict(v) for k,v in self.tokens.items()},"reasoning":{k:asdict(v) for k,v in self.nodes.items()}}}
