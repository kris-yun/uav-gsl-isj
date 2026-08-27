#!/usr/bin/env python3
"""Freeze H02_RECONSTRUCTED_CHALLENGE_V1 context identity before outcomes.

This script does not read source truth, source margins, Gate results, bridge
scores, or localization errors. It discovers surviving House02 context-bank
states using structural files only and writes a deterministic manifest with
SHA256 provenance. The frozen 201-coordinate carrier grid is supplied
separately and is hashed here only as a geometry contract.

Required context files:
  estimated_wind.csv
  measured_hit_probability.csv
  candidate_manifest.csv
  candidate_support_alignment.csv
  source_posterior.csv

The adaptive candidate_manifest inside a surviving context is NOT required to
have 201 rows. The replacement challenge queries the separately frozen 201-row
geometry manifest when rebuilding the CTT/PMFS predictive ensemble.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from pathlib import Path

REQ=(
    'estimated_wind.csv',
    'measured_hit_probability.csv',
    'candidate_manifest.csv',
    'candidate_support_alignment.csv',
    'source_posterior.csv',
)
FORBID_NAME=('truth','ground_truth','evaluation','error','margin','verdict','score')


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def infer_seed(path:Path):
    s=str(path)
    pats=(r'[Ss](?:eed)?[_-]?(\d{1,12})',r'_S(\d{1,12})(?:_|/|$)')
    for p in pats:
        m=re.search(p,s)
        if m:return int(m.group(1))
    return None


def infer_update(path:Path):
    s=str(path)
    for p in (r'source_update[_-]?(\d+)',r'update[_-]?(\d+)',r'_u(\d+)(?:_|/|$)'):
        m=re.search(p,s,re.I)
        if m:return int(m.group(1))
    return None


def discover(roots):
    found={}
    for root in roots:
        root=root.resolve()
        for f in root.rglob('estimated_wind.csv'):
            d=f.parent
            if all((d/x).is_file() for x in REQ):
                found[str(d.resolve())]=d.resolve()
    return [found[k] for k in sorted(found)]


def header(path:Path):
    try:
        with path.open(newline='',encoding='utf-8-sig') as f:
            r=csv.reader(f); return next(r,[])
    except Exception:return []


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('roots',nargs='+',type=Path)
    ap.add_argument('--carrier-manifest',type=Path,required=True,
                    help='frozen 201-row geometry-only House02 carrier manifest')
    ap.add_argument('--out-csv',type=Path,required=True)
    ap.add_argument('--out-json',type=Path,required=True)
    a=ap.parse_args()
    if not a.carrier_manifest.is_file(): raise SystemExit('missing carrier manifest')
    with a.carrier_manifest.open(newline='',encoding='utf-8-sig') as f:
        carriers=list(csv.DictReader(f))
    if len(carriers)!=201: raise SystemExit(f'carrier manifest must contain 201 rows, got {len(carriers)}')

    dirs=discover(a.roots)
    rows=[]
    seen=set()
    for d in dirs:
        # Structural files must not themselves advertise evaluation/truth fields.
        bad=[]
        for name in REQ:
            cols=[x.lower() for x in header(d/name)]
            for c in cols:
                if any(tok in c for tok in FORBID_NAME): bad.append(f'{name}:{c}')
        seed=infer_seed(d); update=infer_update(d)
        key=(str(d),seed,update)
        if key in seen: continue
        seen.add(key)
        row={
            'case_id':f'h02_ctx_{len(rows):04d}',
            'context_dir':str(d),
            'seed':seed if seed is not None else '',
            'source_update_id':update if update is not None else '',
            'structural_header_forbidden_tokens':';'.join(sorted(set(bad))),
        }
        for name in REQ: row[f'sha256_{name}']=sha256(d/name)
        rows.append(row)

    if not rows: raise SystemExit('no structurally complete context directories found')
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    manifest_sha=sha256(a.out_csv)
    distinct_seeds=sorted({str(r['seed']) for r in rows if str(r['seed'])})
    payload={
        'contract':'H02_RECONSTRUCTED_CHALLENGE_V1_CONTEXT_FREEZE',
        'selection_is_outcome_blind':True,
        'legacy_hard28_recreated':False,
        'context_count':len(rows),
        'distinct_inferred_seeds':distinct_seeds,
        'carrier_manifest_rows':201,
        'carrier_manifest_sha256':sha256(a.carrier_manifest),
        'context_manifest_csv_sha256':manifest_sha,
        'ctt_rebuild_contract':{
            'contract_family':'CTT_V13_TRUTH_FREE_TRACE_BANK_V1',
            'method_seed':20260818,
            'transport_substream':6077111455669390931,
            'transport_members':8,
            'timesteps':200,
            'delta_time':0.2,
            'noise_standard_deviation':0.5,
            'source_truth_used':False,
        },
        'next_step':('Freeze this JSON/CSV before generating any new source-margin, '
                     'Gate, bridge, or localization outcome. Rebuild predictive banks '
                     'for every frozen context on the separately frozen 201-coordinate grid.'),
    }
    a.out_json.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(json.dumps(payload,indent=2))

if __name__=='__main__': main()
