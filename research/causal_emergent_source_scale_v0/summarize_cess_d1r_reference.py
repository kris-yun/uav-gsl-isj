#!/usr/bin/env python3
"""Reference-bank integrity/quality summary only. No partition selection."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd

EPS=1e-12

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    p=pd.read_csv(a.panel,sep="\t")
    assert len(p)==168 and p.source_id.nunique()==168

    rows=[]
    all_ok=True
    for i,r in p.iterrows():
        arr=[]
        for rep in range(1,17):
            seed=2026105000+16*i+rep
            f=a.data_root/r.source_id/f"rep_{rep:02d}_seed_{seed}"/"pooled.npy"
            if not f.exists():
                all_ok=False
                continue
            x=np.load(f,allow_pickle=False)
            if x.shape!=(10,30) or not np.isfinite(x).all() or (x<0).any():
                raise RuntimeError(f"invalid pooled array {f}")
            arr.append(x.astype(np.float64))
        if len(arr)!=16:
            continue
        z=np.stack(arr)
        a8=z[:8]; b8=z[8:]
        pa=(a8>0).mean(axis=0).reshape(-1)
        pb=(b8>0).mean(axis=0).reshape(-1)
        den=np.linalg.norm(pa)*np.linalg.norm(pb)
        cos=float(pa@pb/den) if den>0 else float("nan")
        ma=a8.mean(axis=0).reshape(-1)
        mb=b8.mean(axis=0).reshape(-1)
        rel=float(np.linalg.norm(ma-mb)/(np.linalg.norm((ma+mb)/2)+EPS))
        rows.append({
          "panel_index":int(i),
          "source_id":r.source_id,
          "first8_last8_encounter_profile_cosine":cos,
          "first8_last8_raw_mean_relative_l2":rel,
          "median_total_mass":float(np.median(z.sum(axis=(1,2)))),
          "median_zero_fraction":float(np.median((z<=0).mean(axis=(1,2)))),
        })

    df=pd.DataFrame(rows)
    if not all_ok or len(df)!=168:
        result={
          "state":"CESS_D1R_INFRA_STOP",
          "expected_sources":168,
          "complete_sources":int(len(df)),
        }
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
        raise SystemExit(30)

    result={
      "state":"CESS_D1R_REFERENCE_BANK_READY",
      "sources":168,
      "realizations_per_source":16,
      "total_realizations":2688,
      "pooled_shape":[10,30],
      "encounter_profile_cosine_median":float(np.nanmedian(df.first8_last8_encounter_profile_cosine)),
      "encounter_profile_cosine_q10":float(np.nanquantile(df.first8_last8_encounter_profile_cosine,.10)),
      "raw_mean_relative_l2_median":float(np.median(df.first8_last8_raw_mean_relative_l2)),
      "raw_mean_relative_l2_q90":float(np.quantile(df.first8_last8_raw_mean_relative_l2,.90)),
      "median_total_mass_range":[float(df.median_total_mass.min()),float(df.median_total_mass.max())],
      "median_zero_fraction_range":[float(df.median_zero_fraction.min()),float(df.median_zero_fraction.max())],
      "scientific_decision":None,
      "note":"Reference-bank quality summary only. No partition/scale/mainline decision."
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(a.out.with_name("CESS_D1R_SOURCE_QUALITY.tsv"),sep="\t",index=False)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
