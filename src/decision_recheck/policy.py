"""Code-enforced request scope and finite resource budgets."""
from __future__ import annotations
import ipaddress
import math
import re
import socket
import time
from urllib.parse import urlsplit,unquote,parse_qs
from .models import DEFAULT_LIMITS
class PolicyError(ValueError):
    pass
class BudgetExceeded(RuntimeError):
    pass

def check_url(url: str, permissions: dict, *, resolve: bool=True) -> None:
    try:
        parsed=urlsplit(url)
        port=parsed.port
    except ValueError as error:
        raise PolicyError("Invalid URL.") from error
    if parsed.scheme not in ("http","https") or not parsed.hostname:
        raise PolicyError("Only explicitly allowed HTTP(S) URLs can be read.")
    if parsed.username or parsed.password:
        raise PolicyError("URLs containing credentials are not allowed.")
    path=unquote(parsed.path).lower()
    if re.search(r"/(logout|signout|delete|destroy|checkout|payment|purchase|unsubscribe)(/|$)",path) or any(str(v).lower() in ("delete","destroy","purchase","cancel","logout","unsubscribe") for values in parse_qs(parsed.query).values() for v in values):
        raise PolicyError("Known mutating routes are outside this review scope.")
    hostname=parsed.hostname.lower().rstrip(".")
    allowed=[str(v).lower().rstrip(".") for v in permissions.get("allowed_hosts",[])]
    if hostname not in allowed and parsed.netloc.lower() not in allowed:
        raise PolicyError(f"Host is outside the declared scope: {hostname}")
    if permissions.get("allow_private_network",False) is not True:
        try:
            addresses=[ipaddress.ip_address(hostname)]
        except ValueError:
            if not resolve:
                return
            try:
                addresses=[ipaddress.ip_address(v[4][0]) for v in socket.getaddrinfo(hostname,port or (443 if parsed.scheme=="https" else 80),type=socket.SOCK_STREAM)]
            except OSError as error:
                raise PolicyError("The declared host could not be resolved.") from error
        if any(not address.is_global for address in addresses):
            raise PolicyError("Private, loopback and metadata addresses require explicit test permission.")

def check_action(action: str, permissions: dict) -> None:
    if action not in permissions.get("allowed_actions",["read","assert_text"]):
        raise PolicyError(f"Action is not allowed: {action}")
    if action in ("click","fill","download") and permissions.get("allow_test_writes",False) is not True:
        raise PolicyError("Interactive actions require a declared synthetic test environment.")

class Budget:
    def __init__(self,limits:dict|None=None):
        self.limits={**DEFAULT_LIMITS,**(limits or {})}
        for key,value in self.limits.items():
            if key in DEFAULT_LIMITS and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 or (key!="timeout_seconds" and not isinstance(value,int))):
                raise ValueError("Invalid resource limit: "+key)
        self.started=time.monotonic()
        self.model_calls=0
        self.browser_actions=0
        self.reserved_tokens=0
        self.actual_tokens=0
    def check_time(self):
        if time.monotonic()-self.started>=self.limits["timeout_seconds"]:
            raise BudgetExceeded("Run deadline reached.")
    def remaining_seconds(self,maximum=20):
        self.check_time()
        return min(maximum,self.limits["timeout_seconds"]-(time.monotonic()-self.started))
    def consume_action(self):
        self.check_time()
        if self.browser_actions>=self.limits["max_browser_actions"]:
            raise BudgetExceeded("Browser action limit reached.")
        self.browser_actions+=1
    def consume_model(self,reserved_tokens:int=1000):
        self.check_time()
        if self.model_calls>=self.limits["max_model_calls"]:
            raise BudgetExceeded("Model call limit reached.")
        if self.reserved_tokens+reserved_tokens>self.limits["max_tokens"]:
            raise BudgetExceeded("Token reservation limit reached.")
        self.model_calls+=1
        self.reserved_tokens+=reserved_tokens
    def usage(self):
        return {"model_calls":self.model_calls,"browser_actions":self.browser_actions,"reserved_tokens":self.reserved_tokens,"actual_tokens":self.actual_tokens,"elapsed_seconds":round(time.monotonic()-self.started,3),"monetary_cost":None,"monetary_status":"unavailable"}


def resolve_addresses(hostname,port,permissions):
    try:
        addresses=[ipaddress.ip_address(hostname)]
    except ValueError:
        try:
            addresses=list(dict.fromkeys(ipaddress.ip_address(v[4][0]) for v in socket.getaddrinfo(hostname,port,type=socket.SOCK_STREAM)))
        except OSError as error:
            raise PolicyError("The declared host could not be resolved.") from error
    if not addresses or (permissions.get("allow_private_network",False) is not True and any(not address.is_global for address in addresses)):
        raise PolicyError("Connection-time address validation rejected the destination.")
    return addresses

def browser_resolver_rules(permissions):
    rules=[]
    for entry in permissions.get("allowed_hosts",[]):
        try:
            literal=ipaddress.ip_address(entry)
            hostname=str(literal)
            port=443
        except ValueError:
            parsed=urlsplit("//"+entry)
            hostname=parsed.hostname
            port=parsed.port or 443
        if not hostname or not re.fullmatch(r"[A-Za-z0-9_.:-]+",hostname):
            raise PolicyError("Browser hosts must be exact ASCII/IDNA hostnames or IP literals.")
        address=resolve_addresses(hostname,port,permissions)[0]
        host="["+hostname+"]" if ":" in hostname else hostname
        target="["+str(address)+"]" if address.version==6 else str(address)
        rules.append("MAP "+host+" "+target)
    rules.append("MAP * ~NOTFOUND")
    return ", ".join(rules)
