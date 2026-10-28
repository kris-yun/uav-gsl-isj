"""Fetch/audit the official fixed-array data without inventing mobile readings.

Only measurement schema, timestamp/finite-value checks and an unlabelled shape
statistic are reported. No source-error rate, gate error rate or M1 motion score.
"""
from __future__ import annotations
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import urllib.request
import numpy as np


def read_url(url):
    with urllib.request.urlopen(url,timeout=40) as f:return f.read()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data-dir",required=True)
    p.add_argument("--output",default="results/orebro_qualification_audit.json")
    p.add_argument("--download",action="store_true")
    p.add_argument("--commit",default="d5a55a0fc5e77b95456fbb7be62bc8154508dbee")
    args=p.parse_args()
    root=Path(args.data_dir);root.mkdir(parents=True,exist_ok=True)
    manifest_path=root/"download_manifest.json"
    if args.download:
        if args.commit:
            commit=args.commit
        else:
            commit=json.loads(read_url("https://api.github.com/repos/jburgues/Orebro3DSEN/commits/master"))["sha"]
        meta=json.loads(read_url(f"https://api.github.com/repos/jburgues/Orebro3DSEN/contents/logs?ref={commit}"))
        files=[]
        for item in sorted(meta,key=lambda x:x["name"]):
            if not item["name"].endswith(".csv"):continue
            url=f"https://raw.githubusercontent.com/jburgues/Orebro3DSEN/{commit}/logs/{item['name']}"
            data=read_url(url)
            if len(data)!=item["size"]:raise ValueError("Unexpected downloaded size")
            path=root/item["name"];path.write_bytes(data)
            files.append({"file":item["name"],"bytes":len(data),"sha256":sha256(data).hexdigest(),"url":url})
        for name in ["README.md","LICENSE","log_wsn.py"]:
            (root/name).write_bytes(read_url(f"https://raw.githubusercontent.com/jburgues/Orebro3DSEN/{commit}/{name}"))
        manifest={"repository":"https://github.com/jburgues/Orebro3DSEN","commit":commit,
                  "license":"GPL-3.0; original LICENSE retained","files":files}
        manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
    manifest=json.loads(manifest_path.read_text())
    reports=[]
    for item in manifest["files"]:
        path=root/item["file"]
        if sha256(path.read_bytes()).hexdigest()!=item["sha256"]:raise ValueError("Raw hash mismatch")
        with path.open(encoding="mac_roman",newline="") as f:
            rows=list(csv.reader(f))
        header=rows[0]
        data=np.asarray(rows[1:],float)
        channels=[i for i,x in enumerate(header) if x.startswith("C_")]
        if len(channels)!=27 or data.shape[1]!=38:raise ValueError("Unexpected data schema")
        t=data[:,0];y=data[:,channels]
        finite=np.isfinite(y).all(axis=1)
        positive=np.maximum(y,0.)
        total=positive.sum(axis=1)
        good=finite & (total>0)
        shape=np.zeros_like(positive)
        shape[good]=positive[good]/total[good,None]
        adjacent=good[1:]&good[:-1]
        shape_l1=np.abs(shape[1:]-shape[:-1]).sum(axis=1)[adjacent]
        dt=np.diff(t)
        reports.append({"file":item["file"],"sha256":item["sha256"],"rows":len(data),
                        "columns":len(header),"concentration_channels":len(channels),
                        "header":header,"first_timestamp":float(t[0]),"last_timestamp":float(t[-1]),
                        "timestamp_span":float(t[-1]-t[0]),"time_strictly_increasing":bool(np.all(dt>0)),
                        "dt_min_median_max":np.quantile(dt,[0,.5,1]).tolist(),
                        "nonfinite_raw_values":int(np.count_nonzero(~np.isfinite(y))),
                        "negative_raw_values":int(np.count_nonzero(y<0)),
                        "all_nonpositive_frames":int(np.count_nonzero(total<=0)),
                        "adjacent_normalized_shape_l1_quantiles":np.quantile(shape_l1,[0,.5,.9,.99,1]).tolist()
                            if len(shape_l1) else [],
                        "shape_statistic_scope":"descriptive only; no labelled gate false-positive/negative rates"})
    out={"scope":"PUBLIC_RECORDED_FIXED_ARRAY_QUALIFICATION_AUDIT_ONLY",
         "source":manifest["repository"],"commit":manifest["commit"],"download_manifest":manifest,
         "experiments":reports,
         "qualification_conclusion":{
             "record_timestamp_order":"measured per-file; see values",
             "sensor_response_calibration":"repository describes calibration, current dynamic/error details not independently validated",
             "local_wind_per_probe":"UNAVAILABLE; two common wind columns are not 27 local vectors",
             "physical_meter_coordinates":"NOT_INFERRED_FROM_C_ijk index labels",
             "shape_stability":"descriptive statistic only, not coherence proof",
             "same_air_parcel":"UNKNOWN",
             "forward_uniform_error_bound":"UNKNOWN",
             "mobile_counterfactuals":"UNAVAILABLE; fixed array data cannot certify new trajectories",
             "M1_localization_performance":"NOT_EVALUATED"}}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"output":str(dest),"runs":len(reports),"rows":sum(x["rows"] for x in reports),
                      "commit":manifest["commit"],"scope":out["scope"]}))


if __name__=="__main__":main()
