"""Validate recorded native evidence, with no silent analytic fallback."""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    path=Path(args.manifest)
    result={"status":"UNRESOLVED_DATA_OR_INTERFACE","issues":[],"checked_files":[],
            "native_performance_evaluated":False,"method_failed":False}
    if not path.exists():
        result["issues"].append(f"Manifest absent: {path}")
    else:
        m=json.loads(path.read_text())
        if m.get("status")!="FROZEN":result["issues"].append("Protocol/data manifest is not frozen")
        if m.get("budget_s")!=300.0:result["issues"].append("World budget must be exactly 300 s")
        for key in m.get("required_freeze_fields",[]):
            if key not in m.get("freeze",{}):result["issues"].append(f"Unfrozen field: {key}")
        if not m.get("cases"):result["issues"].append("No verified native cases")
        for case in m.get("cases",[]):
            for key in ["world_id","house_id","configuration_id","plume_realization_id","split",
                        "t_start_s","t_end_s","counterfactual_query_supported","files"]:
                if key not in case:result["issues"].append(f"Case missing {key}")
            if case.get("t_end_s",0)-case.get("t_start_s",0)<300:
                result["issues"].append(f"Insufficient time support for {case.get('world_id')}")
            if case.get("counterfactual_query_supported") is not True:
                result["issues"].append(f"Fixed-trajectory records cannot support new actions: {case.get('world_id')}")
            for f in case.get("files",[]):
                target=Path(f["path"]).expanduser()
                if not target.is_absolute():target=path.parent/target
                if not target.is_file():
                    result["issues"].append(f"Missing actual native file: {target}");continue
                h=sha256()
                with target.open("rb") as stream:
                    for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
                digest=h.hexdigest()
                ok=digest==f.get("sha256")
                result["checked_files"].append({"path":str(target),"sha256":digest,"matches":ok})
                if not ok:result["issues"].append(f"Native file hash mismatch: {target}")
        if not result["issues"]:
            result["status"]="MANIFEST_AND_BYTES_CHECKED_INTERFACE_RECEIPTS_STILL_REVIEW_REQUIRED"
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"issues":len(result["issues"]),"output":str(out)}))
    return 4 if result["issues"] else 0


if __name__=="__main__":sys.exit(main())
