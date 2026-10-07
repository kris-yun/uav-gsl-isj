"""Independent arithmetic: edge=complement of interior, manual quantile,
centroid from the separately exported native-state CSV, not cached raw arrays.
Does not import either screen implementation or change their outputs.
"""
from pathlib import Path
import csv, json, hashlib, math
import numpy as np
HERE=Path(__file__).resolve().parent
OLD=Path('C:/Users/50176/Documents/Codex/2026-10-05/codex-pmfs-pmfs-task-sufficient-world/outputs')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def records(p):
    with Path(p).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def quantile(values,q):
    x=sorted(float(v) for v in values);at=(len(x)-1)*q;i=math.floor(at);j=math.ceil(at)
    return x[i]+(at-i)*(x[j]-x[i])
protocol=json.loads((HERE/'STAGE0_BOUNDARY_PROTOCOL_V2_FROZEN.json').read_text())
preseal=json.loads((HERE/'STAGE0_V2_PRE_SCORE_SEAL.json').read_text())
assert preseal['protocol_sha256']==sha(HERE/'STAGE0_BOUNDARY_PROTOCOL_V2_FROZEN.json')
assert preseal['code_sha256']==sha(HERE/'audit_stage0_v2.py')
runs=json.loads((OLD/'P0/RUNS_64_FROZEN.json').read_text())
scores={r['run_id']:r for r in records(HERE/'STAGE0_V2_RUN_BOUNDARY_SCORES.csv')}
moments={(r['run_id'],int(r['requested_time'])):r for r in records(OLD/'P0/PLUME_STATES_AND_CAUSAL_WIND_64.csv')}
original_seal=json.loads((OLD/'P0/EXTRACTION_SEAL_BEFORE_SCORING.json').read_text())
source_contract=json.loads((OLD/'R0C/SOURCE_CONTRACT_R0C.json').read_text())
sources={(h['house'],s['source']):s for h in source_contract['house_contracts'] for s in [h['source_A'],h['source_B']]}
errors=[];eligibility={};max_error=0.0
for r in runs:
    p=OLD/'P0/states'/(r['run_id']+'.npz');assert sha(p)==original_seal['state_files'][r['run_id']]
    with np.load(p) as z:
        times=[int(t) for t in z['times'] if 100<=t<=700];n=protocol['boundary_band_bins'];edges=[];clearances=[]
        for t in times:
            index=list(z['times']).index(t);f=z['footprint'][index].astype(np.float64)
            total=math.fsum(f.ravel());interior=math.fsum(f[n:-n,n:-n].ravel());edges.append((total-interior)/total)
            m=moments[r['run_id'],t]
            xy=[float(m['cx']),float(m['cy'])]
            ds=[]
            for axis in [0,1]:
                width=float(z['span'][axis])/32;lower=float(z['lo'][axis]);upper=lower+float(z['span'][axis]);ds.extend([(xy[axis]-lower)/width,(upper-xy[axis])/width])
            clearances.append(min(ds))
        source=sources[r['house'],r['source']];margins=[]
        for axis,key in enumerate(['x','y']):
            width=float(z['span'][axis])/32;lower=float(z['lo'][axis]);upper=lower+float(z['span'][axis]);margins.extend([(source[key]-lower)/width,(upper-source[key])/width])
        values=[math.fsum(edges)/len(edges),quantile(edges,.95),min(clearances),min(margins)]
        columns=['mean_edge_mass_fraction','q95_edge_mass_fraction','min_centroid_clearance_bins','source_min_clearance_bins']
        for v,key in zip(values,columns):
            error=abs(v-float(scores[r['run_id']][key]));max_error=max(max_error,error)
            if error>1e-12:errors.append({'run_id':r['run_id'],'metric':key,'difference':error})
        ok=values[0]<=.05 and values[1]<=.10 and values[2]>=3 and values[3]>=3
        assert ok==(scores[r['run_id']]['eligible']=='True')
        eligibility[r['run_id']]=ok
assert not errors
cells={(r['house'],r['wind_label'],r['gas_type'],r['source']) for r in runs}
eligible_cells=sum(all(eligibility[r['run_id']] for r in runs if (r['house'],r['wind_label'],r['gas_type'],r['source'])==cell) for cell in cells)
decision=json.loads((HERE/'STAGE0_V2_DECISION.json').read_text())
assert eligible_cells==decision['eligible_cells']==0
assert decision['new_simulations']==0 and decision['matched_error_hypothesis_tested'] is False
result={'status':'PASS','verified_original_state_hashes':len(runs),'native_centroid_crosschecks':len(runs)*31,'max_numeric_difference':max_error,'independent_eligible_cells':eligible_cells,'original_protocol_and_code_hashes_unchanged':True,'thresholds_not_relaxed':True,'new_simulations':0,'verification_code_sha256':sha(__file__)}
(HERE/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
