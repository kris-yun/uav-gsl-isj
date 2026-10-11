"""Static input/support inventory only: never estimates h, predicts ppm or scores sources."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import json, csv, importlib.util, hashlib, time
import numpy as np

BASE = Path(__file__).resolve().parents[2]
RK = BASE / 'outputs/PMFS_RK0_RESPONSE_STATE_NECESSITY_20261010'
M2 = BASE / 'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
OUT = Path(__file__).resolve().parent
START = time.perf_counter()

def csvrows(p):
    with p.open(encoding='utf-8', newline='') as f: return list(csv.DictReader(f))

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

spec = importlib.util.spec_from_file_location('static_gaden_decode', RK/'source/verify_raw_receiver_queries.py')
raw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(raw)
index = json.loads((RK/'reference_contribution_cache/CONTRIBUTION_CACHE_RESULT.json').read_text(encoding='utf-8'))
banks = ['C7_0','C7_1','K2_0','K2_1']
data = {}
for bank in banks:
    frames = []
    for e in index['frames']:
        if e['bank'] != bank: continue
        p = RK/'reference_contribution_cache'/e['cache_relative_path']
        with np.load(p) as z:
            f = z['filaments'].copy()
            assert z['contributions'].shape == (len(f),10)
            assert z['native_totals'].shape == (10,)
        frames.append((int(e['frame']),int(e['exposure_weight']),f))
    assert len(frames)==49 and sum(w for _,w,_ in frames)==50
    data[bank] = frames

old_eval = ['C7_2','C7_3','K2_2','K2_3']
for bank in old_eval:
    weights = {}
    for r in csvrows(M2/'native_reference_evidence/realizations'/bank/'QUERY_PHYSICAL_LINEAGE.csv'):
        if r['membership_branch']!='0': continue
        frame=int(r['selected_frame']);weights[frame]=weights.get(frame,0)+1
    data[bank] = [(frame,w,raw.snapshot(M2/'native_reference_evidence/realizations'/bank/'bank'/f'iteration_{frame}')['filaments']) for frame,w in sorted(weights.items())]

origin=np.array([-7.55,-7.88],dtype=np.float32)
fixed=json.loads((RK/'REFERENCE_ONLY_STATE_BOUNDARIES.json').read_text(encoding='utf-8'))

def keyarray(f,cuts,model):
    xy=np.floor((f[:,:2]-origin)/np.float32(.25)).astype(np.int64)
    cl=np.zeros(len(f),dtype=np.int64) if model=='U' else (f[:,2].astype(float)>=cuts[0]).astype(np.int64)*2+(f[:,3].astype(float)>=cuts[1]).astype(np.int64)
    return [(int(i),int(j),int(c)) for (i,j),c in zip(xy,cl)]

def support(train,cuts,model):
    out=set()
    for bank in train:
        for _,_,f in data[bank]: out.update(keyarray(f,cuts,model))
    return out

def cov(bank, train_support, cuts, model):
    miss=total=complete=0; unique_missing=set()
    for _,w,f in data[bank]:
        keys=keyarray(f,cuts,model); bad=[k for k in keys if k not in train_support]
        miss+=len(bad)*w;total+=len(keys)*w;complete+=int(len(bad)==0)*w;unique_missing.update(bad)
    return dict(bank=bank,total_planned_exposures=50,fully_supported_exposures=complete,uncovered_particle_exposures=miss,total_particle_exposures=total,distinct_uncovered_keys=len(unique_missing))

folds=[]
for ci in (0,1):
    for ki in (0,1):
        train=[f'C7_{ci}',f'K2_{ki}'];test=[f'C7_{1-ci}',f'K2_{1-ki}']
        # Only summary of training-state geometry for the proposed partition; no kernel fitting.
        fit=np.concatenate([np.repeat(f[:,[2,3]].astype(np.float64),w,axis=0) for b in train for _,w,f in data[b]])
        cuts=tuple(map(float,np.median(fit,axis=0)))
        entry=dict(fold=f'C{ci}K{ki}',train=train,whole_realization_test=test,training_particle_exposures=len(fit),training_only_median_z_m=cuts[0],training_only_median_sigma_cm=cuts[1],models={})
        for name in ['U','S']:
            pooled=support(train,cuts,name)
            source_support={b[:2]:support([b],cuts,name) for b in train}
            intersection=source_support['C7']&source_support['K2']
            entry['models'][name]=dict(pooled_active_keys=len(pooled),source_C7_active_keys=len(source_support['C7']),source_K2_active_keys=len(source_support['K2']),both_candidate_supported_keys=len(intersection),test_support={b:dict(pooled=cov(b,pooled,cuts,name),C7_kernel=cov(b,source_support['C7'],cuts,name),K2_kernel=cov(b,source_support['K2'],cuts,name),strict_both_candidate_common=cov(b,intersection,cuts,name)) for b in test},old_heldout_pooled_support=[cov(b,pooled,cuts,name) for b in old_eval])
        folds.append(entry)

result=dict(status='STATIC_SUPPORT_INVENTORY_ONLY_NO_KERNEL_FIT_OR_NEW_SCORE',cache_frames=196,cache_poses=10,cache_pairs=2242960,cache_fully_supports_test_reference_crosspose_readout=True,reference_banks=banks,old_heldout_banks=old_eval,folds=folds,
    proposed_compute=dict(pooled_U_S_kernels=8,source_conditional_U_kernels=8,source_conditional_S_optional_kernels=8,source_conditioned_R_not_needed=True,new_native_phi_queries=0,new_physics=0,new_ROS=0,primary_fold_whole_bank_test_exposures=400,unique_independent_gas_banks=4,folds_are_overlapping_not_independent=True),
    parameters_summary_only=dict(existing_global_z_split_m=fixed['z_split_m'],existing_global_sigma_split_cm=fixed['sigma_split_cm'],global_existing_cuts_are_test_distribution_informed_under_inner_crossfit=True),
    scope='Only frame/count/cache schema/support key inventory. Existing stored phi/native totals were shape checked and were not used to fit h or evaluate performance.',wall_seconds=time.perf_counter()-START,
    script_SHA256=sha(Path(__file__)),cache_index_SHA256=sha(RK/'reference_contribution_cache/CONTRIBUTION_CACHE_RESULT.json'))
(OUT/'coverage_feasibility_counts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=result['status'],wall_seconds=result['wall_seconds'],folds=[dict(fold=x['fold'],train=x['train'],test=x['whole_realization_test'],cuts=[x['training_only_median_z_m'],x['training_only_median_sigma_cm']],U=[r['pooled']['fully_supported_exposures'] for r in x['models']['U']['test_support'].values()],S=[r['pooled']['fully_supported_exposures'] for r in x['models']['S']['test_support'].values()],Uc_common=[r['strict_both_candidate_common']['fully_supported_exposures'] for r in x['models']['U']['test_support'].values()],Sc_common=[r['strict_both_candidate_common']['fully_supported_exposures'] for r in x['models']['S']['test_support'].values()]) for x in folds]),ensure_ascii=False,indent=2))
