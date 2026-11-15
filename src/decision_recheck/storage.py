"""Evidence files are confined to a new run directory."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
def write_json(path:Path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
def artifact(output:Path,artifact_id:str,data:bytes|str,extension:str="json",media_type:str="application/json"):
    raw=data.encode("utf-8") if isinstance(data,str) else data
    path=Path("artifacts")/f"{artifact_id}.{extension}"
    target=output/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
    return {"id":artifact_id,"path":path.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"size_bytes":len(raw),"media_type":media_type}
def load_bundle(path:str|Path):
    path=Path(path)
    file=path/"bundle.json" if path.is_dir() else path
    return json.loads(file.read_text(encoding="utf-8-sig")),file.parent
