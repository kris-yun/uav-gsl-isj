"""Read-only, source-ID legality audit. No concentration/ranking analysis."""
import csv,hashlib,json,sys,subprocess
from pathlib import Path
import numpy as np
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927');sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    out=ROOT/'actual_support_audit_v2';out.mkdir(exist_ok=False)
    bank=TemplateBank.load(ROOT/'example_banks/h03_model_only.npz')
    belief_file=Path('/home/zyc/brg_closedloop_20260927/native_software_smoke_02_raw/beliefs.jsonl')
    actual=json.loads(belief_file.read_text().splitlines()[0]);legal=set(actual['free_cells']);original=set(bank.cells.tolist())
    removed=sorted(original-legal);assert len(removed)==9 and not legal-original
    path=Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House03/OccupancyGrid3D.csv')
    header={};values=[]
    for line in path.read_text().splitlines():
        line=line.strip()
        if line.startswith('#'):header[line.split()[0]]=line.split()[1:]
        elif line and line!=';':values.extend(map(int,line.split()))
    dims=list(map(int,header['#num_cells']));minimum=list(map(float,header['#env_min(m)']));dx=float(header['#cell_size(m)'][0])
    z=int((.2-minimum[2])/dx);raw=np.array(values,np.uint8).reshape(dims[2],dims[0],dims[1]);plane=raw[z]
    # Exact VGR serialization semantics and Native 3x3 occupancy reduction.
    reduced=np.array([int(np.all(plane[i*3:(i+1)*3,j*3:(j+1)*3]==0))
        for j in range(bank.ny) for i in range(bank.nx)],np.uint8)
    fine_reduce_path=out/'native_fine_reduced_occupancy.u8';reduced.tofile(fine_reduce_path)
    verified_path=out/'native_verified_legal_occupancy.u8'
    command=['/dev/shm/brg_native_support_probe',str(bank.nx),str(bank.ny),str(bank.dx),str(bank.ox),str(bank.oy),'2.0','0.0',str(fine_reduce_path),str(verified_path)]
    verified=subprocess.run(command,capture_output=True,text=True,check=True)
    (out/'native_prune.log').write_text(verified.stdout+verified.stderr)
    verified_mask=np.fromfile(verified_path,np.uint8)
    assert np.flatnonzero(verified_mask).tolist()==actual['free_cells'],'actual Native mask cannot be reproduced from fine-grid reduction + Native prune'
    probe=np.fromfile(ROOT/'legal_support/h03_occupancy.u8',np.uint8)
    rows=[]
    with Path('/home/zyc/aod_house03_f1_full624_20260927/protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv').open() as f:truth=list(csv.DictReader(f,delimiter='\t'))
    truth_ids={r['source_id'] for r in truth}
    for c in removed:
        i=c%bank.nx;j=c//bank.nx;sid=f'pmfs_{i}_{j}';take=bank.ids.index(sid)
        block=plane[i*3:(i+1)*3,j*3:(j+1)*3];counts={str(v):int((block==v).sum()) for v in (0,1,2)}
        reason=('NATIVE_COARSE_OCCUPANCY_BLOCKED: VGR treats raw 1/2 as blocked and Native rejects a 3x3 cell containing any blocked fine voxel'
            if reduced[c]==0 else 'NATIVE_REACHABILITY_PRUNE: initially free coarse cell is not reached from fixed start')
        rows.append({'source_id':sid,'grid_index':c,'grid_i':i,'grid_j':j,'x_m':float(bank.xy[take,0]),'y_m':float(bank.xy[take,1]),
            'z_m':.2,'is_frozen_truth':sid in truth_ids,'raw_3x3_counts':counts,'raw_3x3_values':block.tolist(),
            'native_before_reachability_free':bool(reduced[c]),'bank_native_probe_without_fine_grid_free':bool(probe[c]),'reason':reason})
    lost=[r['source_id'] for r in truth if int(r['pmfs_i'])+bank.nx*int(r['pmfs_j']) not in legal]
    report={'decision':'BRG_HOLD_FROZEN_TRUTH_EXCLUDED_FROM_NATIVE_SUPPORT' if lost else 'NATIVE_SUPPORT_AUDIT_TRUTHS_RETAINED',
        'formal_campaign_started':False,'scored_runs':0,'native_candidates':len(legal),'model_bank_candidates':len(original),
        'frozen_truth_count':12,'retained_truth_count':12-len(lost),'excluded_truth_ids':lost,'removed_candidates':rows,
        'source_blind_runtime_start_xy':[2.,0.],'z_slice_index':z,'actual_initialized_time_s':actual['time_s'],
        'occupancy_sha256':sha(path),'native_beliefs_sha256':sha(belief_file),'original_model_bank_sha256':sha(ROOT/'example_banks/h03_model_only.npz'),
        'fine_grid_reduction_count':int(reduced.sum()),'native_reachability_removes_from_reduced_grid':int(reduced.sum()-verified_mask.sum()),
        'native_fixed_rule_actual_mask_byte_exact_match':True,
        'candidate_support_was_not_masked_or_changed':True,'no_truth_case_deleted':True,
        'bank_generation_continues_independently':True,'new_gaden_plumes':0,'next_action':'Return IDs/reasons to user; no scored campaign until explicit resolution'}
    (out/'RESULT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    with (out/'REMOVED_NATIVE_CANDIDATES.tsv').open('w') as f:
        w=csv.writer(f,delimiter='\t');w.writerow(['source_id','grid_index','grid_i','grid_j','x_m','y_m','is_frozen_truth','raw_zero_count','raw_one_count','raw_two_count','reason'])
        for r in rows:w.writerow([r[k] for k in ['source_id','grid_index','grid_i','grid_j','x_m','y_m','is_frozen_truth']]+[r['raw_3x3_counts'][str(v)] for v in (0,1,2)]+[r['reason']])
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
