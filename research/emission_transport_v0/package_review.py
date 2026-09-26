"""Package implementation and actual W0 primitives; preserve all local files."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

p=argparse.ArgumentParser()
p.add_argument("--root",type=Path,required=True)
p.add_argument("--out",type=Path,required=True)
a=p.parse_args()
a.root=a.root.resolve()
if a.out.exists(): raise FileExistsError("refuse to overwrite a review package")
roots=[a.root/"research/emission_transport_v0",a.root/"evidence/emission_transport_v0"]
files=[a.root/name for name in (".gitattributes","collect_fixed_primitive.sh",
                                "primitive_readonly_inventory.sh")]
for root in roots:
    for f in root.rglob("*"):
        if not f.is_file() or "__pycache__" in f.parts or f.name.endswith((".tar.gz",".pyc")):
            continue
        files.append(f)
sha=lambda b:hashlib.sha256(b).hexdigest()
items={f.relative_to(a.root).as_posix():f.read_bytes() for f in sorted(files)}
provenance={"branch":subprocess.check_output(["git","branch","--show-current"],cwd=a.root,text=True).strip(),
            "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=a.root,text=True).strip(),
            "decision":json.loads((a.root/"evidence/emission_transport_v0/DEVELOPMENT_DECISION.json").read_text())["DEVELOPMENT_DECISION"],
            "new_full_plumes":0,"new_primitive_random_samples":0,
            "scientific_decision":None,
            "excluded":"retained downloaded tar archives and Python caches; no files deleted"}
items["PROVENANCE.json"]=(json.dumps(provenance,indent=2)+"\n").encode()
checksums="".join(f"{sha(data)}  {name}\n" for name,data in sorted(items.items()))
items["SHA256SUMS"]=checksums.encode()
a.out.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.out,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,data in sorted(items.items()): z.writestr(name,data)
with zipfile.ZipFile(a.out) as z:
    assert z.testzip() is None
    lines=z.read("SHA256SUMS").decode().splitlines()
    for line in lines:
        expected,name=line.split("  ",1)
        assert sha(z.read(name))==expected,name
    assert len(lines)==len(z.namelist())-1
result={**provenance,"path":str(a.out.resolve()),"bytes":a.out.stat().st_size,
        "sha256":sha(a.out.read_bytes()),"internal_files_verified":len(lines)}
a.out.with_suffix(".metadata.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,ensure_ascii=False,indent=2))
