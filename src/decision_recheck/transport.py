"""Connection-time destination pinning while retaining the original HTTP/TLS origin."""
from __future__ import annotations
import ssl
import httpcore
import httpx
from .policy import check_url,resolve_addresses

class PinnedBackend(httpcore.SyncBackend):
    def __init__(self,permissions):
        self.permissions=permissions
    def connect_tcp(self,host,port,timeout=None,local_address=None,socket_options=None):
        hostname=host.decode("ascii") if isinstance(host,bytes) else str(host)
        rendered="["+hostname+"]" if ":" in hostname else hostname
        check_url("https://"+rendered+":"+str(port)+"/",self.permissions,resolve=False)
        address=resolve_addresses(hostname,port,self.permissions)[0]
        # A numeric target avoids a second attacker-controlled hostname resolution.
        # The pool still owns the original origin and therefore the TLS server name.
        return super().connect_tcp(str(address),port,timeout,local_address,socket_options)

class CoreStream(httpx.SyncByteStream):
    def __init__(self,stream):
        self.stream=stream
    def __iter__(self):
        yield from self.stream
    def close(self):
        self.stream.close()

class ScopedTransport(httpx.BaseTransport):
    def __init__(self,permissions):
        self.pool=httpcore.ConnectionPool(ssl_context=ssl.create_default_context(),network_backend=PinnedBackend(permissions),max_connections=2,retries=0)
    def handle_request(self,request):
        incoming=httpcore.Request(method=request.method,url=str(request.url),headers=request.headers.raw,content=request.stream,extensions=request.extensions)
        response=self.pool.handle_request(incoming)
        return httpx.Response(status_code=response.status,headers=response.headers,stream=CoreStream(response.stream),extensions=response.extensions)
    def close(self):
        self.pool.close()
