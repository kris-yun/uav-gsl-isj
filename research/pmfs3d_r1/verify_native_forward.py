"""Four-case reconstruction check only; no Oracle-2D/3D execution or truth rank."""
import argparse
import csv
import hashlib
import json
import struct
import subprocess
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--audit',type=Path,required=True)
p.add_argument('--inputs',type=Path,required=True)
p.add_argument('--binary',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
audit=json.loads(a.audit.read_text());results=[]
for case in audit['cases']:
    prepared=a.inputs/case['case'];out=a.out/case['case']
    subprocess.run([str(a.binary),str(prepared),str(prepared/'config.csv'),'native',str(out)],check=True)
    original=a.audit.parent/'frozen_inputs'/case['case']/'context_bank'/f"source_update_{int(case['terminal']['source_update_id']):04d}"
    ids={r['candidate_id'] for r in case['active_candidates']}
    predictions={}
    for cid in sorted(ids):
        raw=(out/'maps'/f'{cid}.f32').read_bytes()
        predictions[cid]=struct.unpack('<'+'f'*(len(raw)//4),raw)
    diffs=[]
    with (original/'candidate_support_alignment.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            cid=row['candidate_id']
            if cid in ids:
                diffs.append(abs(predictions[cid][int(row['cell_index'])]-float(row['simulated_hit_probability'])))
    result=dict(case=case['case'],matched_entries=len(diffs),max_abs_hit_map_error=max(diffs),
                pass_native_forward=max(diffs)<1e-7,
                binary_sha256=hashlib.sha256(a.binary.read_bytes()).hexdigest())
    results.append(result)
    print(json.dumps(result),flush=True)
    assert result['pass_native_forward'], result
(a.out/'NATIVE_FORWARD_PARITY.json').write_text(json.dumps(dict(cases=results,oracle_executed=False,truth_rank_computed=False),indent=2,sort_keys=True)+'\n')
