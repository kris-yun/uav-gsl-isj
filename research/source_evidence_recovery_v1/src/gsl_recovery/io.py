"""Auditable JSON serialization and hashes (never pickle external inputs)."""
from dataclasses import asdict, is_dataclass
from pathlib import Path
import json, hashlib, numpy as np

def json_default(obj):
    if is_dataclass(obj): return asdict(obj)
    if isinstance(obj,np.ndarray): return obj.tolist()
    if isinstance(obj,np.generic): return obj.item()
    if isinstance(obj,Path): return str(obj)
    raise TypeError(type(obj).__name__)

def write_json(path, obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=json_default,allow_nan=False)+'\n',encoding='utf-8')

def read_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
