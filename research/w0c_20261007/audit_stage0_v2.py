"""Conservative all-boundary eligibility screen; no new plume simulation."""
from pathlib import Path
import csv, json, hashlib, datetime
import numpy as np
HERE=Path(__file__).resolve().parent
OLD=Path('C:/Users/50176/Documents/Codex/2026-10-05/codex-pmfs-pmfs-task-sufficient-world/outputs')
P0=OLD/'P0'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(name,obj): (HERE/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
def csvout(name,rows):
    with (HERE/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
if (HERE/'STAGE0_V2_DECISION.json').exists(): raise RuntimeError('Completed V2 must be preserved.')
protocol=json.loads((HERE/'STAGE0_BOUNDARY_PROTOCOL_V2_FROZEN.json').read_text())
dump('STAGE0_V2_PRE_SCORE_SEAL.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protocol_sha256':sha(HERE/'STAGE0_BOUNDARY_PROTOCOL_V2_FROZEN.json'),'code_sha256':sha(__file__),'new_simulations':0,'perturbations_generated':0})
runs=json.loads((P0/'RUNS_64_FROZEN.json').read_text());assert len(runs)==64
seal=json.loads((P0/'EXTRACTION_SEAL_BEFORE_SCORING.json').read_text())
contract=json.loads((OLD/'R0C/SOURCE_CONTRACT_R0C.json').read_text())
assert contract['decision']=='R0C0_SOURCE_CONTRACT_PASS'
sources={(h['house'],s['source']):s for h in contract['house_contracts'] for s in [h['source_A'],h['source_B']]}
lineage=[]
for h in contract['house_contracts']:
    p=P0/(h['house']+'_OccupancyGrid3D.csv');assert sha(p)==h['occupancy_sha256']
    lineage.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
n=protocol['boundary_band_bins'];boundary=np.ones((32,32),bool);boundary[n:-n,n:-n]=False
rows=[];traces=[]
for r in runs:
    p=P0/'states'/(r['run_id']+'.npz');digest=sha(p);assert digest==seal['state_files'][r['run_id']]
    lineage.append({'path':str(p),'bytes':p.stat().st_size,'sha256':digest})
    source=sources[(r['house'],r['source'])];assert source['individually_eligible'] and source['raw_3d_free'] and source['z']==.3
    with np.load(p) as z:
        keep=(z['times']>=100)&(z['times']<=700)&z['valid'];assert keep.sum()==31
        fp=z['footprint'][keep].astype(float);assert np.isfinite(fp).all() and (fp>=0).all()
        total=fp.sum((1,2));assert (total>0).all()
        edge=fp[:,boundary].sum(axis=1)/total
        width=z['span'][:2]/32;lo=z['lo'][:2];hi=lo+z['span'][:2]
        centroid=z['raw'][keep,:2]
        clearance=np.column_stack(((centroid-lo)/width,(hi-centroid)/width)).min(axis=1)
        source_xy=np.array([source['x'],source['y']]);source_margin=float(np.r_[(source_xy-lo)/width,(hi-source_xy)/width].min())
        mean=float(edge.mean());q95=float(np.quantile(edge,.95));margin=float(clearance.min())
        conditions=[mean<=protocol['edge_mass_mean_max'],q95<=protocol['edge_mass_q95_max'],margin>=protocol['centroid_clearance_min_bins'],source_margin>=protocol['source_clearance_min_bins']]
        reason=','.join(name for name,ok in zip(['mean_edge_mass','q95_edge_mass','centroid_clearance','source_clearance'],conditions) if not ok)
        rows.append({'house':r['house'],'wind':r['wind_label'],'gas':r['gas_type'],'source':r['source'],'realization':r['realization'],'run_id':r['run_id'],'mean_edge_mass_fraction':mean,'q95_edge_mass_fraction':q95,'min_centroid_clearance_bins':margin,'source_min_clearance_bins':source_margin,'eligible':all(conditions),'failed_conditions':reason})
        for i,t in enumerate(z['times'][keep]):traces.append({'run_id':r['run_id'],'time_s':int(t),'union_edge_mass_fraction':float(edge[i]),'centroid_min_clearance_bins':float(clearance[i])})
cells=[]
for key in sorted({(r['house'],r['gas'],r['wind'],r['source']) for r in rows}):
    h,g,w,s=key;rs=[r for r in rows if (r['house'],r['gas'],r['wind'],r['source'])==key];assert len(rs)==4
    cells.append({'house':h,'gas':g,'wind':w,'source':s,'worst_run_mean_edge_mass_fraction':max(r['mean_edge_mass_fraction'] for r in rs),'worst_run_q95_edge_mass_fraction':max(r['q95_edge_mass_fraction'] for r in rs),'minimum_centroid_clearance_bins':min(r['min_centroid_clearance_bins'] for r in rs),'eligible_realizations':sum(r['eligible'] for r in rs),'eligible':all(r['eligible'] for r in rs)})
eligible=[r for r in cells if r['eligible']];selected=[]
for house in protocol['allowed_houses']:
    cases=[r for r in eligible if r['house']==house]
    if cases:selected.append(cases[0])
if len(selected)==1:selected += [r for r in eligible if r['house']==selected[0]['house'] and r['source']!=selected[0]['source']][:1]
csvout('STAGE0_V2_RUN_BOUNDARY_SCORES.csv',rows);csvout('STAGE0_V2_TIME_BOUNDARY_TRACES.csv',traces);csvout('STAGE0_V2_CELL_ELIGIBILITY.csv',cells);csvout('STAGE0_V2_INPUT_LINEAGE_SHA256.csv',lineage)
result={'status':'W0C_STAGE0_CLEAN_BASE_AVAILABLE' if selected else 'W0C_STAGE0_NO_CLEAN_BASE_HOLD','baseline_runs_checked':len(rows),'cells_checked':len(cells),'eligible_runs':sum(r['eligible'] for r in rows),'eligible_cells':len(eligible),'selected_cases':selected,'protocol_sha256':sha(HERE/'STAGE0_BOUNDARY_PROTOCOL_V2_FROZEN.json'),'code_sha256':sha(__file__),'new_simulations':0,'perturbations_generated':0,'matched_error_hypothesis_tested':False,'claim':'A failed prerequisite does not establish a null matched-error mechanism.'}
dump('STAGE0_V2_DECISION.json',result)
print(json.dumps({'decision':result,'cells':cells},indent=2))
