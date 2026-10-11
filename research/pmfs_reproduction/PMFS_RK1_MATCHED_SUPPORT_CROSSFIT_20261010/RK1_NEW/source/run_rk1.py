"""One frozen, cache-only matched-support crossfit. No new response/physics query."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,csv,json,hashlib,math,time
import numpy as np

ARMS=('U','S','C_C7','C_K2')
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvout(p,v):
    assert v
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(v[0]));w.writeheader();w.writerows(v)
def classes(f,cuts):
    ij=np.floor((f[:,:2]-np.array([-7.55,-7.88],dtype=np.float32))/np.float32(.25)).astype(np.int64)
    cl=(f[:,2].astype(float)>=cuts[0]).astype(np.int64)*2+(f[:,3].astype(float)>=cuts[1]).astype(np.int64)
    return [(int(i),int(j),int(c)) for (i,j),c in zip(ij,cl)]
def accumulate(frames,bank,Q,cuts,fine):
    count={};sums={}
    for frame,x in sorted(frames[bank].items()):
        kk=classes(x['f'],cuts);w=x['w']
        for n,k in enumerate(kk):
            if k not in Q:continue
            key=k if fine else (k[0],k[1],-1)
            if key not in count:count[key]=0;sums[key]=np.zeros(10,dtype=np.float64)
            count[key]+=w;sums[key]+=x['phi'][n].astype(float)*w
    return count,sums
def pool(a,b):
    ca,sa=a;cb,sb=b;cc={};ss={}
    for key in sorted(set(ca)|set(cb)):
        cc[key]=ca.get(key,0)+cb.get(key,0)
        ss[key]=sa.get(key,np.zeros(10))+sb.get(key,np.zeros(10))
    return cc,ss
def kernels(a):return {k:a[1][k]/a[0][k] for k in a[0]}
def amount(count,h,pose):return math.fsum(n*float(h[k][pose]) for k,n in count.items())
def model_metrics(pp,truthmap):
    rr=[]
    for fold in sorted({r['fold'] for r in pp}):
        for role in ['train','test']:
            for bank in sorted({r['bank'] for r in pp if r['fold']==fold and r['role']==role}):
                z=[r for r in pp if r['fold']==fold and r['role']==role and r['bank']==bank and r['membership_branch']==0]
                assert len(z)==50
                selected='C_'+truthmap[bank]
                for arm in ARMS+('C_ORACLE',):
                    col=selected if arm=='C_ORACLE' else arm
                    ee=[r[col+'_prediction_ppm']-r['target_phi64_ppm'] for r in z]
                    rr.append(dict(fold=fold,role=role,bank=bank,arm=arm,generating_condition_analysis_only=truthmap[bank],C_selected_analysis_only=selected if arm=='C_ORACLE' else '',planned_exposures=50,independent_realizations=1,MSE_ppm2=math.fsum(e*e for e in ee)/50,mean_signed_error_ppm=math.fsum(ee)/50,MAE_ppm=math.fsum(abs(e) for e in ee)/50,event_errors_native_F32=sum(r[col+'_event']!=r['native_F32_event'] for r in z),event_errors_phi64=sum(r[col+'_event']!=r['target_phi64_event'] for r in z),tail_alone_positive_events=sum(r['tail_alone_event'] for r in z),eligible_response_fraction=math.fsum(r['target_Q64_ppm'] for r in z)/math.fsum(r['target_phi64_ppm'] for r in z),oracle_scope='same native Q-outside tail and native state counts; no localization/source classification'))
    return rr
def analyze(out,pp,cond):
    before={p.name:sha(p) for p in sorted(out.glob('*.csv'))}
    dump(out/'PRE_ANALYSIS_PREDICTION_SHA256.json',before)
    # Generator role is selected only now, after all hypothesis predictions froze.
    truthmap=load(out/'ANALYSIS_ONLY_GENERATOR_MAPPING_FROZEN.json')
    dump(out/'POST_FREEZE_GENERATOR_MAPPING.json',truthmap)
    metrics=model_metrics(pp,truthmap);csvout(out/'BANK_METRICS_ANALYSIS.csv',metrics)
    paired=[]
    for fold in sorted({r['fold'] for r in pp}):
        for bank in sorted({r['bank'] for r in pp if r['fold']==fold and r['role']=='test'}):
            m={r['arm']:r for r in metrics if r['fold']==fold and r['role']=='test' and r['bank']==bank}
            u,s,c=m['U']['MSE_ppm2'],m['S']['MSE_ppm2'],m['C_ORACLE']['MSE_ppm2']
            tol=max(1e-12,1e-10*max(u,s,c))
            paired.append(dict(fold=fold,bank=bank,generating_condition_analysis_only=truthmap[bank],U_MSE_ppm2=u,S_MSE_ppm2=s,C_ORACLE_MSE_ppm2=c,U_to_S_MSE_reduction=u-s,S_to_C_MSE_reduction=s-c,U_to_C_MSE_reduction=u-c,U_to_S_relative_reduction=(u-s)/u if u else 'ZERO_BASELINE',S_to_C_relative_reduction=(s-c)/s if s else 'ZERO_BASELINE',comparison_tolerance_ppm2=tol,S_better_than_U=u-s>tol,C_better_than_S=s-c>tol,C_better_than_U=u-c>tol))
    csvout(out/'TEST_BANK_PAIRED_COMPARISONS.csv',paired)
    summaries=[]
    for fold in sorted({r['fold'] for r in cond}):
        z=[r for r in cond if r['fold']==fold];supported=[r for r in z if r['test_C7_count']>0 and r['test_K2_count']>0]
        active=[r for r in supported if abs(r['train_C7_minus_K2_h'])>3e-13]
        same=sum(r['train_C7_minus_K2_h']*r['test_C7_minus_K2_h']>0 for r in active if abs(r['test_C7_minus_K2_h'])>3e-13)
        opposite=sum(r['train_C7_minus_K2_h']*r['test_C7_minus_K2_h']<0 for r in active if abs(r['test_C7_minus_K2_h'])>3e-13)
        w=[min(r['test_C7_count'],r['test_K2_count']) for r in supported]
        summaries.append(dict(fold=fold,train_common_key_pose_rows=len(z),test_both_source_supported_rows=len(supported),nonzero_training_difference_rows=len(active),same_sign_test_rows=same,opposite_sign_test_rows=opposite,test_nearzero_among_active=len(active)-same-opposite,weighted_difference_MSE=math.fsum(ww*(r['train_C7_minus_K2_h']-r['test_C7_minus_K2_h'])**2 for r,ww in zip(supported,w))/sum(w) if sum(w) else None,interpretation='Descriptive correlated oracle class responses; not independent trials, unique height cause or deployment input'))
    dump(out/'CONDITIONAL_DIFFERENCE_SUMMARY.json',summaries)
    result=dict(execution_status='PASS_COMPLETED_FROZEN_MATCHED_SUPPORT_CROSSFIT',test_banks=4,test_exposures=200,independent_new_realizations=0,new_phi_calls=0,new_simulation=0,new_network_training=0,kernel_tables_fitted=8,arms=list(ARMS),S_MSE_gains=sum(r['S_better_than_U'] for r in paired),C_oracle_over_S_MSE_gains=sum(r['C_better_than_S'] for r in paired),C_oracle_over_U_MSE_gains=sum(r['C_better_than_U'] for r in paired),equal_bank_mean_test_MSE={a:math.fsum(r['MSE_ppm2'] for r in metrics if r['role']=='test' and r['arm']==a)/4 for a in ARMS+('C_ORACLE',)},per_source_directions={g:dict(S_over_U=[r['S_better_than_U'] for r in paired if r['generating_condition_analysis_only']==g],C_over_S=[r['C_better_than_S'] for r in paired if r['generating_condition_analysis_only']==g]) for g in ['C7','K2']},all_four_S_improve=all(r['S_better_than_U'] for r in paired),all_four_C_over_S_improve=all(r['C_better_than_S'] for r in paired),science_scope=['Old inspected bank, same geometry/static wind/trajectory; no new prospective task.','All arms share exact native oracle tail. Gains constrain Q only; tail is not a deployed prediction.','C_ORACLE selects generating condition after prediction freeze, has more conditioning/parameters and is nonnested with S.','No source posterior, source classification success, CSCG or new transport model is evaluated.'])
    dump(out/'RK1_RESULT.json',result)
    for n,h in before.items():assert sha(out/n)==h,n
    return result
def main(parent,out):
    started=time.perf_counter();contract=load(out/'contract.json')
    assert sha(out/'contract.json')==(out/'PRE_RUN_CONTRACT_SHA256.txt').read_text().split()[0]
    for n,h in contract['executed_source_SHA256'].items():assert sha(out/'source'/n)==h,n
    for n,h in contract['input_SHA256'].items():assert sha(parent/n)==h,n
    cache=parent/'RK0_NEW/reference_contribution_cache';index=load(cache/'CONTRIBUTION_CACHE_RESULT.json')
    first=load(cache/'FIRST_NATIVE_ANCHOR.json');e=next(x for x in index['frames'] if x['bank']==first['reference_bank'] and x['frame']==first['frame'])
    with np.load(cache/e['cache_relative_path']) as a:
        phi=a['contributions'][:,0];v=np.float32(0)
        for p in phi:v=np.float32(v+p)
        assert float(v)==first['native_ppm']
    dump(out/'FIRST_ANCHOR_RECHECK.json',dict(status='PASS_BEFORE_ANY_KERNEL_FIT',ppm=float(v),native_ppm=first['native_ppm'],absolute_difference=0,new_query_calls=0))
    frames={b:{} for b in index['reference_ids']};anchors=[]
    for e in index['frames']:
        p=cache/e['cache_relative_path'];assert sha(p)==e['cache_SHA256']
        with np.load(p) as z:
            f=z['filaments'].copy();phi=z['contributions'].copy();native=z['native_totals'].copy()
        assert f.dtype==np.float32 and phi.dtype==np.float32 and phi.shape==(len(f),10)
        assert np.isfinite(phi).all() and (phi>=0).all()
        serial=np.cumsum(phi,axis=0,dtype=np.float32)[-1]
        assert np.array_equal(serial.view(np.uint32),native.view(np.uint32))
        frames[e['bank']][e['frame']]=dict(f=f,phi=phi,native=native,w=e['exposure_weight'])
        for q in e['native_query_checks']:
            v=float(native[q['pose_index']]);assert v==q['native_cpp_ppm']
            anchors.append(dict(bank=e['bank'],query_id=q['query_id'],frame=e['frame'],pose_id=q['pose_index'],cached_native_F32_ppm=v,native_CPP_ppm=q['native_cpp_ppm'],absolute_difference=abs(v-q['native_cpp_ppm'])))
    assert len(anchors)==204;csvout(out/'NATIVE_ANCHOR_RECHECK.csv',anchors)
    aliases={r['query_id']:r for r in rows(cache/'RECEPTOR_ALIAS_51_TO_10.csv')}
    m2=parent/'PARENT_M2M3_FROZEN/M2_FROZEN'
    schedules={b:rows(m2/'native_reference_evidence/realizations'/b/'QUERY_PHYSICAL_LINEAGE.csv') for b in frames}
    allpred=[];allcond=[];foldmeta=[];supports=[]
    for side in [0,1]:
        fold=f'T{side}_E{1-side}';train=[f'C7_{side}',f'K2_{side}'];test=[f'C7_{1-side}',f'K2_{1-side}']
        pop=np.concatenate([np.repeat(x['f'][:,[2,3]].astype(float),x['w'],axis=0) for b in train for x in frames[b].values()]);cuts=list(map(float,np.median(pop,axis=0)))
        sets={b:set(k for x in frames[b].values() for k in classes(x['f'],cuts)) for b in train}
        Q=sets[train[0]]&sets[train[1]];assert Q
        for k in sorted(Q):supports.append(dict(fold=fold,cell_i=k[0],cell_j=k[1],class_id=k[2]))
        a_xy=accumulate(frames,train[0],Q,cuts,False);b_xy=accumulate(frames,train[1],Q,cuts,False)
        a_cl=accumulate(frames,train[0],Q,cuts,True);b_cl=accumulate(frames,train[1],Q,cuts,True)
        fit={'U':pool(a_xy,b_xy),'S':pool(a_cl,b_cl),'C_C7':a_xy,'C_K2':b_xy}
        h={a:kernels(fit[a]) for a in ARMS}
        eligible_denoms={a:sum(fit[a][0].values()) for a in ARMS}
        assert eligible_denoms['U']==eligible_denoms['S']==eligible_denoms['C_C7']+eligible_denoms['C_K2']
        meta=dict(fold=fold,train_banks=train,test_banks=test,z_split_m=cuts[0],sigma_split_cm=cuts[1],common_fine_keys=len(Q),shared_XY_keys=len(h['U']),active_cell_classes={a:len(h[a]) for a in ARMS},eligible_particle_exposure_denominators=eligible_denoms,all_training_exposures={b:sum(len(x['f'])*x['w'] for x in frames[b].values()) for b in train},zero_denominator_policy='Counts include all selected-Q particles including explicit zero response; excluded particles are the same oracle tail for every arm')
        foldmeta.append(meta);dump(out/(fold+'_FIT_METADATA.json'),meta)
        for arm in ARMS:
            rr=[]
            for key in sorted(h[arm]):
                for pose in range(10):
                    r=dict(fold=fold,arm=arm,cell_i=key[0],cell_j=key[1],class_id=key[2],pose_id=pose,particle_exposure_denominator=fit[arm][0][key],phi_sum_ppm=float(fit[arm][1][key][pose]),h_ppm_per_particle=float(h[arm][key][pose]));rr.append(r)
            csvout(out/(fold+'_KERNEL_'+arm+'.csv'),rr)
        # Test-native conditional class moments are descriptive output, never fit inputs.
        tA=accumulate(frames,test[0],Q,cuts,True);tB=accumulate(frames,test[1],Q,cuts,True)
        for key in sorted(Q):
            for pose in range(10):
                n1,n2=a_cl[0][key],b_cl[0][key];t1,t2=tA[0].get(key,0),tB[0].get(key,0)
                h1=float(a_cl[1][key][pose]/n1);h2=float(b_cl[1][key][pose]/n2)
                v1=float(tA[1][key][pose]/t1) if t1 else 'UNSUPPORTED';v2=float(tB[1][key][pose]/t2) if t2 else 'UNSUPPORTED'
                allcond.append(dict(fold=fold,cell_i=key[0],cell_j=key[1],class_id=key[2],pose_id=pose,train_C7_count=n1,train_K2_count=n2,train_C7_h=h1,train_K2_h=h2,train_C7_minus_K2_h=h1-h2,test_C7_count=t1,test_K2_count=t2,test_C7_h=v1,test_K2_h=v2,test_C7_minus_K2_h=v1-v2 if t1 and t2 else 'UNSUPPORTED',not_fit_input=True))
        for role,banks in [('train',train),('test',test)]:
            for bank in banks:
                for ev in schedules[bank]:
                    block=int(ev['block_id']);branch=int(ev['membership_branch']);qid=f'receiver_b{block}_v{branch}';pose=int(aliases[qid]['pose_index']);frame=int(ev['selected_frame']);x=frames[bank][frame]
                    kk=classes(x['f'],cuts);mask=np.array([k in Q for k in kk],dtype=bool);countXY={};countCL={}
                    for key,keep in zip(kk,mask):
                        if not keep:continue
                        cell=(key[0],key[1],-1);countXY[cell]=countXY.get(cell,0)+1;countCL[key]=countCL.get(key,0)+1
                    ph=x['phi'][:,pose];q=math.fsum(map(float,ph[mask]));tail=math.fsum(map(float,ph[~mask]));full=math.fsum(map(float,ph));assert math.isclose(q+tail,full,rel_tol=2e-12,abs_tol=3e-13)
                    native=float(x['native'][pose]);r=dict(fold=fold,role=role,bank=bank,block_id=block,membership_branch=branch,frame=frame,pose_id=pose,total_particles=len(kk),eligible_particles=int(mask.sum()),tail_particles=int((~mask).sum()),eligible_mask_SHA256=hashlib.sha256(np.packbits(mask,bitorder='little').tobytes()).hexdigest(),target_Q64_ppm=q,tail_Qoutside64_ppm=tail,target_phi64_ppm=full,native_full_F32_ppm=native,phi64_minus_native_F32_ppm=full-native,target_phi64_event=int(full>float(np.float32(.1))),native_F32_event=int(np.float32(native)>np.float32(.1)),tail_alone_event=int(tail>float(np.float32(.1))),full_target_near_threshold=abs(full-float(np.float32(.1)))<=3e-7+5e-6*abs(full))
                    for arm in ARMS:
                        val=amount(countCL if arm=='S' else countXY,h[arm],pose);pred=tail+val
                        assert math.isfinite(pred) and pred>=0
                        r[arm+'_Q_prediction_ppm']=val;r[arm+'_prediction_ppm']=pred;r[arm+'_event']=int(pred>float(np.float32(.1)));r[arm+'_changed_event_vs_tail']=int(r[arm+'_event']!=r['tail_alone_event'])
                    allpred.append(r)
        print(json.dumps(dict(fold=fold,status='FITTED_AND_ALL_HYPOTHESES_PREDICTED',common_keys=len(Q),tables=4,prediction_rows=len([r for r in allpred if r['fold']==fold])),ensure_ascii=False),flush=True)
    assert len(allpred)==408 and len([r for r in allpred if r['role']=='test' and r['membership_branch']==0])==200
    csvout(out/'COMMON_SUPPORT_FINE_KEYS.csv',supports);csvout(out/'PREDICTIONS_BLIND.csv',allpred);csvout(out/'CLASS_CONDITIONAL_RESPONSE_DIFFERENCES.csv',allcond)
    dump(out/'FIT_METADATA.json',foldmeta)
    csvout(out/'MODEL_COMPLEXITY.csv',[dict(fold=f['fold'],arm=a,active_keys=f['active_cell_classes'][a],receiver_coefficients=f['active_cell_classes'][a]*10,particle_exposure_denominator=f['eligible_particle_exposure_denominators'][a]) for f in foldmeta for a in ARMS])
    result=analyze(out,allpred,allcond);result['producer_wall_s']=time.perf_counter()-started
    dump(out/'RK1_RESULT.json',result);print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.parent,a.out)
