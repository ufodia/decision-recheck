"""Bounded source readers shared by capture and live FreshCtx checks."""
from __future__ import annotations
import json
from urllib.parse import urljoin
import httpx
from .models import resolve_field
from .policy import Budget,PolicyError,check_url
from .storage import now
from .transport import ScopedTransport

class SourceError(RuntimeError):
    pass

def fetch_http(url:str,permissions:dict,budget:Budget)->bytes:
    for _ in range(6):
        budget.check_time()
        check_url(url,permissions,resolve=False)
        remaining=budget.remaining_seconds(15)
        with httpx.Client(timeout=remaining,follow_redirects=False,trust_env=False,transport=ScopedTransport(permissions)) as client:
            with client.stream("GET",url,headers={"User-Agent":"DecisionRecheck/0.1 source-audit"}) as response:
                if response.status_code in (301,302,303,307,308):
                    location=response.headers.get("location")
                    if not location:
                        raise SourceError("Redirect has no target.")
                    url=urljoin(url,location)
                    continue
                if response.status_code!=200:
                    raise SourceError(f"Source returned HTTP {response.status_code}; content was not treated as proof.")
                data=bytearray()
                for chunk in response.iter_bytes():
                    budget.check_time()
                    data.extend(chunk)
                    if len(data)>budget.limits["max_response_bytes"]:
                        raise SourceError("Source exceeded the configured response size.")
                return bytes(data)
    raise SourceError("Redirect limit reached.")

def read_source(source:dict,brief:dict,budget:Budget)->dict:
    budget.check_time()
    if "inline" in source:
        raw=json.dumps(source["inline"],ensure_ascii=False,allow_nan=False).encode("utf-8")
        value=source["inline"]
    elif source.get("format","json")=="html":
        from .browser import read_html_source
        return read_html_source(source,brief,budget)
    else:
        raw=fetch_http(source["url"],brief["permissions"],budget)
        value=json.loads(raw,parse_constant=lambda v:(_ for _ in ()).throw(ValueError("Non-finite JSON number"))) if source.get("format","json")=="json" else raw.decode("utf-8")
    if len(raw)>budget.limits["max_response_bytes"]:
        raise SourceError("Source exceeded the configured response size.")
    fields=source.get("fields") or ({"text":"$"} if isinstance(value,str) else {str(k):str(k) for k in value} if isinstance(value,dict) else {"value":"$"})
    try:
        selected={key:resolve_field(value,path) for key,path in fields.items()}
    except (KeyError,IndexError,TypeError) as error:
        raise SourceError("A declared source field is unavailable; extraction needs review.") from error
    if any(v is None or (isinstance(v,str) and not v.strip()) for v in selected.values()):
        raise SourceError("A declared source field is empty; extraction needs review.")
    # The comparison boundary includes extractor, scope and selected values.
    return {"raw":raw,"values":selected,"checked_at":now(),
            "observation":{"extractor":"json-fields-v1" if source.get("format","json")=="json" else "text-v1","fields":fields,"scope":brief["scope"],"values":selected}}

def source_reader(source:dict,brief:dict,budget:Budget,holder:list):
    def reader():
        record=read_source(source,brief,budget)
        holder.append(record)
        return record["observation"]
    return reader
