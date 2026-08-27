#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

def read(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def arm(uuid):
    u=uuid.lower()
    if u.endswith('_off') or '_off_' in u:return 'legacy_off_trajectory'
    if u.endswith('_on') or '_on_' in u:return 'legacy_on_trajectory'
    return 'structural_other'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('context_manifest',type=Path); ap.add_argument('verify_json',type=Path)
    ap.add_argument('--out-csv',type=Path,required=True); ap.add_argument('--out-json',type=Path,required=True); a=ap.parse_args()
    rr=read(a.context_manifest); ver=json.loads(a.verify_json.read_text())
    if ver.get('verdict')!='H02_RECONSTRUCTED_CHALLENGE_V1_BANK_VERIFY_PASS': raise SystemExit('bank verify not PASS')
    if ver.get('context_count')!=len(rr): raise SystemExit('context count mismatch')
    seen=set(); out=[]
    for r in rr:
        ident=(r['run_uuid'],r['source_update_id'])
        if ident in seen: raise SystemExit('duplicate run/update')
        seen.add(ident)
        seed=str(r['seed']).strip()
        if not seed: raise SystemExit('blank seed not allowed for cluster contract')
        out.append({**r,'cluster_id':f'seed:{seed}','legacy_trajectory_class':arm(r['run_uuid'])})
    clusters=sorted({r['cluster_id'] for r in out}); runs=sorted({r['run_uuid'] for r in out})
    ignored=sorted({r.get('structural_header_forbidden_tokens','') for r in out if r.get('structural_header_forbidden_tokens','')})
    if len(out)<18 or len(clusters)<3: raise SystemExit('pre-registered atom/cluster minimum not met')
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    payload={'contract':'H02_RECONSTRUCTED_CHALLENGE_V1_ANALYSIS_CONTRACT','pre_outcome':True,
      'context_atoms':len(out),'seed_clusters':clusters,'cluster_count':len(clusters),'run_uuid_count':len(runs),
      'cluster_unit':'seed; OFF/ON runs and repeated source updates within one seed are NOT independent inferential units',
      'ignored_archival_headers':ignored,
      'allowed_model_inputs':['CTT/PMFS predictive member responses','candidate physical coordinates','actual measurement positions/times','measured wind','pose/action/map context','current gas/sensor outcome Y'],
      'forbidden_model_inputs':['source truth','native_score','source_posterior values','wind id oracle','route id','plume seed','simulator phase','future data'],
      'forbidden_feature_audit_pass':'PENDING_FINAL_METHOD_INPUT_AUDIT',
      'selection_outcome_blind':True,'provenance_pass':True}
    a.out_json.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(json.dumps(payload,indent=2))
if __name__=='__main__':main()
