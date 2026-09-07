"""Materialize a self-contained, current-runtime controlled asset bundle."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

CASES = [
    ("H01", "SA", "fast", [-0.6, 1.95, 0.4]), ("H01", "SA", "slow", [-0.6, 1.95, 0.4]),
    ("H01", "SB", "fast", [-0.4, -2.9, -0.3]), ("H01", "SB", "slow", [-0.4, -2.9, -0.3]),
    ("H02", "SA", "fast", [0.0, -1.0, 0.2]), ("H02", "SA", "slow", [0.0, -1.0, 0.2]),
    ("H02", "SB", "fast", [1.0, -2.3, -0.1]), ("H02", "SB", "slow", [1.0, -2.3, -0.1]),
    ("H03", "SA", "fast", [-0.45, 1.9, -0.1]), ("H03", "SA", "slow", [-0.45, 1.9, -0.1]),
    ("H03", "SB", "fast", [8.2, 5.0, -0.2]), ("H03", "SB", "slow", [8.2, 5.0, -0.2]),
]

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--histories', type=Path, required=True); ap.add_argument('--maps', type=Path, required=True); ap.add_argument('--out', type=Path, required=True); a=ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    records=[]
    horizon_s = 240.0
    for h, source, transport, xyz in CASES:
        cid=f'{h}_{source}_{transport}'
        src_hist=a.histories/cid/'measured_history.jsonl'
        if not src_hist.exists(): raise SystemExit(f'missing {src_hist}')
        dest_hist=a.out/'realizations'/cid/'measured_history.jsonl'; dest_hist.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src_hist,dest_hist)
        map_src=a.maps/h/'candidate.csv'; map_dest=a.out/'maps'/h/'candidate.csv'; map_dest.parent.mkdir(parents=True,exist_ok=True)
        if not map_dest.exists(): shutil.copy2(map_src,map_dest)
        records.append({
            'candidate_domain_path': f'maps/{h}/candidate.csv', 'candidate_domain_sha256': sha(map_dest), 'candidate_domain_truth_independent': True,
            'episode_id': cid, 'geometry_identity': f'{h}:current-runtime-map-only', 'history_end_s': horizon_s,
            'history_semantics':'causal_prefixes', 'history_start_s':0.2, 'history_trace_path':f'realizations/{cid}/measured_history.jsonl',
            'history_trace_sha256':sha(dest_hist), 'house':h, 'prefix_times_s':list(range(4,241,4)),
            'realization_id':cid, 'release_intervention_id':'current_runtime_gas10_seed1234', 'runtime_feature_schema_version':'CSTAR_MEASURED_HISTORY_V1',
            'sensor_intervention_id':'current_runtime_sensor_seed12', 'sensor_state_kind':'absent', 'source_id':source,
            'source_xyz_m':xyz, 'split':'heldout', 'transport_intervention_id':f'current_runtime_{h}_{transport}',
        })
    base={'asset_root':'.','contract':'CSTAR_CURRENT_RUNTIME_CONTROLLED_ASSET_V1','created_git_sha':'pending',
          'runtime_contract':'GADEN_V3_CURRENT_RUNTIME_FIXED_SEED_1234','gas_type':10,'sim_time_s':60.1,'raw_dt_s':0.1,
          'sensor_contract':'sensor_model seed12, fixed response, no added noise','route_contract':'CSTAR_SOURCE_BLIND_MAP_COVER_ROUTE_V1',
          'evaluator_only_fields':['source_xyz_m','source_id','house','realization_id','true_gas_ppm','future_gas','future_wind'],
          'forbidden_model_inputs':['true_gas_ppm','future_gas','source_xyz_m','source_id'],'m1_episodes':records}
    for h in ('H01','H02','H03'):
        b=dict(base); b['m1_episodes']=[r for r in records if r['house']==h]; (a.out/'manifests').mkdir(exist_ok=True); (a.out/'manifests'/f'{h}.json').write_text(json.dumps(b,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (a.out/'MANIFEST.json').write_text(json.dumps({'contract':base['contract'],'record_count':len(records),'houses':{h:4 for h in ('H01','H02','H03')},'history_sha256':{r['episode_id']:r['history_trace_sha256'] for r in records}},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'records':len(records),'out':str(a.out)},sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
