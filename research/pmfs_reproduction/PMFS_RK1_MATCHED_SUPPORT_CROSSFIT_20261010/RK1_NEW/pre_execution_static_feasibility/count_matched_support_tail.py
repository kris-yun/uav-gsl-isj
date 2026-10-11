"""Static eligibility/readout-mass audit; no kernel fit, prediction or source score."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,hashlib,time,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
RK=ROOT/'outputs/PMFS_RK0_RESPONSE_STATE_NECESSITY_20261010'
M2=ROOT/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
OUT=Path(__file__).resolve().parent
start=time.perf_counter()
idx=json.loads((RK/'reference_contribution_cache/CONTRIBUTION_CACHE_RESULT.json').read_text(encoding='utf-8'))
origin=np.array([-7.55,-7.88],dtype=np.float32)
allframes={b:{} for b in idx['reference_ids']}
for e in idx['frames']:
    with np.load(RK/'reference_contribution_cache'/e['cache_relative_path']) as a:
        allframes[e['bank']][e['frame']]=dict(f=a['filaments'].copy(),phi=a['contributions'].copy(),w=int(e['exposure_weight']),native=a['native_totals'].copy())
def keys(f,cuts):
    ij=np.floor((f[:,:2]-origin)/np.float32(.25)).astype(np.int64)
    c=(f[:,2].astype(float)>=cuts[0]).astype(np.int64)*2+(f[:,3].astype(float)>=cuts[1]).astype(np.int64)
    return [(int(i),int(j),int(k)) for (i,j),k in zip(ij,c)]
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
events={b:rows(M2/'native_reference_evidence/realizations'/b/'QUERY_PHYSICAL_LINEAGE.csv') for b in idx['reference_ids']}
pose={int(x['block_id']):int(x['stop_id']) for x in rows(M2/'observation_lineage/FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv') if x['membership_branch']=='0'}
ledger=[];folds=[]
for side in (0,1):
    train=[f'C7_{side}',f'K2_{side}'];test=[f'C7_{1-side}',f'K2_{1-side}']
    pop=np.concatenate([np.repeat(x['f'][:,[2,3]].astype(float),x['w'],axis=0) for b in train for x in allframes[b].values()])
    cuts=tuple(map(float,np.median(pop,axis=0)))
    support=[]
    for b in train:
        ss=set()
        for x in allframes[b].values():ss.update(keys(x['f'],cuts))
        support.append(ss)
    common=support[0]&support[1]
    row=dict(fold=f'T{side}_E{1-side}',train=train,test=test,cuts_training_only_z_sigma=list(cuts),both_source_common_fine_keys=len(common),union_fine_keys=len(support[0]|support[1]),training_eligible={})
    for b in train:
        n=eligible=0
        for x in allframes[b].values():
            k=keys(x['f'],cuts);n+=len(k)*x['w'];eligible+=sum(z in common for z in k)*x['w']
        row['training_eligible'][b]=dict(all_particle_exposures=n,eligible_particle_exposures=eligible,fraction=eligible/n)
    row['test_eligibility']={}
    for b in test:
        part=good=allresp=goodresp=0.;tailpositive=bothtail=eligiblepositive=0;eligibility=[]
        perstop={p:dict(eligible_particle_exposures=0,total_particle_exposures=0,eligible_phi_ppm_sum=0.,total_phi_ppm_sum=0.,tail_above_native_threshold=0,events=0) for p in range(10)}
        for ev in events[b]:
            if ev['membership_branch']!='0':continue
            block=int(ev['block_id']);p=pose[block];x=allframes[b][int(ev['selected_frame'])]
            kk=keys(x['f'],cuts); mask=np.array([v in common for v in kk],dtype=bool)
            phi=x['phi'][:,p]
            full=math.fsum(map(float,phi));ep=math.fsum(map(float,phi[mask]));tail=math.fsum(map(float,phi[~mask]))
            assert abs(full-(ep+tail))<=max(1e-12,abs(full)*1e-12)
            nt=len(kk);ng=int(mask.sum());part+=nt;good+=ng;allresp+=full;goodresp+=ep
            ta=int(np.float32(tail)>np.float32(.1));ea=int(np.float32(ep)>np.float32(.1));fa=int(x['native'][p]>np.float32(.1));tailpositive+=ta;eligiblepositive+=ea;bothtail+=int(ta and fa)
            eligibility.append(ep/full if full>0 else None)
            q=perstop[p];q['eligible_particle_exposures']+=ng;q['total_particle_exposures']+=nt;q['eligible_phi_ppm_sum']+=ep;q['total_phi_ppm_sum']+=full;q['tail_above_native_threshold']+=ta;q['events']+=1
            ledger.append(dict(fold=row['fold'],bank=b,block_id=block,pose_id=p,frame=int(ev['selected_frame']),eligible_particles=ng,all_particles=nt,eligible_particle_fraction=ng/nt,eligible_native_particle_phi_sum_ppm=ep,tail_native_particle_phi_sum_ppm=tail,total_native_particle_phi_sum_ppm=full,eligible_response_fraction=ep/full if full else 'NO_NATIVE_RESPONSE',tail_alone_above_native_float32_0p1=ta,eligible_alone_above_native_float32_0p1=ea,native_F_above_threshold=fa))
        for q in perstop.values():
            q['eligible_particle_fraction']=q['eligible_particle_exposures']/q['total_particle_exposures']
            q['eligible_response_fraction']=q['eligible_phi_ppm_sum']/q['total_phi_ppm_sum'] if q['total_phi_ppm_sum'] else None
        nz=[x for x in eligibility if x is not None]
        row['test_eligibility'][b]=dict(exposures=50,total_particle_exposures=int(part),eligible_particle_exposures=int(good),eligible_particle_fraction=good/part,total_native_particle_phi_ppm_sum=allresp,eligible_native_particle_phi_ppm_sum=goodresp,eligible_response_fraction=goodresp/allresp if allresp else None,positive_response_event_count=len(nz),minimum_per_event_eligible_response_fraction=min(nz) if nz else None,median_per_event_eligible_response_fraction=float(np.median(nz)) if nz else None,tail_alone_above_native_threshold_events=tailpositive,eligible_alone_above_native_threshold_events=eligiblepositive,native_positive_events_with_positive_tail=bothtail,perstop=perstop)
    folds.append(row)
out=dict(status='STATIC_MATCHED_SUPPORT_AND_EXISTING_READOUT_MASS_QUALIFICATION',fit_kernels=0,new_predictions=0,new_source_scores=0,new_phi_computation=0,new_simulation=0,folds=folds,scales=dict(ref_banks=4,unique_ref_frames=196,planned_test_exposures=200,unique_test_realizations=4,overlapping_training_not_new_independence=True),tail_scope='Tail is sum of already-cached per-particle native contributions, shared identically across proposed arms. This audit computes only eligibility/readout mass and threshold saturation, not fitted predictions/performance.',wall_seconds=time.perf_counter()-start,script_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(OUT/'matched_support_tail_counts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (OUT/'MATCHED_SUPPORT_TAIL_STATIC_LEDGER.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)
print(json.dumps(dict(status=out['status'],wall_seconds=out['wall_seconds'],summary=[dict(fold=x['fold'],common_keys=x['both_source_common_fine_keys'],test={b:{k:v for k,v in z.items() if k in ('eligible_particle_fraction','eligible_response_fraction','tail_alone_above_native_threshold_events','eligible_alone_above_native_threshold_events','median_per_event_eligible_response_fraction','minimum_per_event_eligible_response_fraction')} for b,z in x['test_eligibility'].items()}) for x in folds]),ensure_ascii=False,indent=2))
