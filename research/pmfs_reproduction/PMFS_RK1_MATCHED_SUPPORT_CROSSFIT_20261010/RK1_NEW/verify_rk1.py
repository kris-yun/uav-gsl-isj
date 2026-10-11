"""Independent cache-only RK1 verifier. Never calls the experiment producer.

No ROS, no new particle readout, no physical simulation. Fits reconstructed here
are verification arithmetic on already frozen cached numbers only.
"""
import sys
sys.dont_write_bytecode = True
import argparse, csv, hashlib, json, math
from pathlib import Path
from collections import Counter
import numpy as np

ATOL = 3e-12
RTOL = 3e-12

def read_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def read_csv(p):
    with Path(p).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def close(a, b, label, atol=ATOL, rtol=RTOL):
    # Most artifact checks are scalar; avoid an array allocator per CSV field.
    if np.ndim(a)==0 and np.ndim(b)==0:
        av,bv=float(a),float(b)
        if not math.isfinite(av) or not math.isfinite(bv) or abs(av-bv)>atol+rtol*abs(bv):
            raise AssertionError(f'{label}: {av} vs {bv}')
        return
    aa, bb = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if aa.shape != bb.shape or not np.all(np.isfinite(aa)) or not np.all(np.isfinite(bb)) or not np.allclose(aa, bb, atol=atol, rtol=rtol):
        diff = np.max(np.abs(aa-bb)) if aa.shape == bb.shape and aa.size else 'shape'
        raise AssertionError(f'{label}: {aa.shape} vs {bb.shape}, maximum difference {diff}')

def integer(x):
    z = float(x)
    assert z == int(z)
    return int(z)

def weighted_middle(x, weights):
    # Search the lower half exposure by stable numeric ordering, not frame means.
    idx = np.argsort(x, kind='stable')
    total = int(np.sum(weights, dtype=np.int64))
    assert total > 0
    cs = np.cumsum(weights[idx],dtype=np.int64)
    lower = int(np.searchsorted(cs,(total+1)//2,side='left'))
    upper = int(np.searchsorted(cs,total//2+1,side='left'))
    return (float(x[idx[lower]])+float(x[idx[upper]]))/2

def fine_keys(f, zcut, scut):
    # The inherited RK0 contract uses native f32 subtraction/division here.
    ij = np.floor((f[:, :2]-np.array([-7.55,-7.88],dtype=np.float32))/np.float32(.25)).astype(np.int64)
    cls = (f[:, 2].astype(np.float64) >= zcut).astype(np.int64)*2+(f[:, 3].astype(np.float64) >= scut).astype(np.int64)
    return np.column_stack((ij,cls))

def load_cache(cache_dir):
    meta = read_json(cache_dir/'CONTRIBUTION_CACHE_RESULT.json')
    assert len(meta['frames']) == 196
    assert len(meta['poses']) == 10
    frames = {}
    anchors = []
    for e in meta['frames']:
        p = cache_dir/e['cache_relative_path']
        assert sha(p) == e['cache_SHA256'], str(p)
        with np.load(p, allow_pickle=False) as z:
            f = z['filaments'].copy()
            phi = z['contributions'].copy()
            nt = z['native_totals'].copy()
            wt = integer(z['planned_time_exposure_weight'])
            fid = integer(z['reference_frame'])
        assert f.dtype == np.dtype('float32') and f.ndim == 2 and f.shape[1] == 4
        assert phi.dtype == np.dtype('float32') and phi.shape == (len(f), 10)
        assert nt.dtype == np.dtype('float32') and nt.shape == (10,)
        assert np.all(np.isfinite(f)) and np.all(np.isfinite(phi)) and np.all(phi >= 0)
        assert wt in (1,2) and wt == e['exposure_weight'] and fid == e['frame']
        # np.sum may use a pairwise accumulator; native C++ is serial float32.
        serial = np.cumsum(phi, axis=0, dtype=np.float32)[-1] if len(phi) else np.zeros(10,np.float32)
        assert np.array_equal(serial.view(np.uint32),nt.view(np.uint32)), (e['bank'],fid)
        frames[(e['bank'],fid)] = dict(f=f,phi=phi,w=wt,native=nt)
        for q in e['native_query_checks']:
            val = float(serial[integer(q['pose_index'])])
            assert val == float(q['native_cpp_ppm']) == float(q['cache_F32_ppm'])
            anchors.append(q)
    assert len(anchors) == 204
    return meta,frames

def independent_fold(frames, train_banks):
    # Concatenate unique snapshots; a duplicate exposure is a weight, not a new independent record.
    f = np.concatenate([v['f'] for (b,_),v in frames.items() if b in train_banks])
    w = np.concatenate([np.full(len(v['f']),v['w'],dtype=np.int64) for (b,_),v in frames.items() if b in train_banks])
    zcut = weighted_middle(f[:,2].astype(np.float64), w)
    scut = weighted_middle(f[:,3].astype(np.float64), w)
    banks = {}
    for b in train_banks:
        sel = [v for (bank,_),v in frames.items() if bank == b]
        ff = np.concatenate([v['f'] for v in sel])
        pp = np.concatenate([v['phi'] for v in sel]).astype(np.float64)
        ww = np.concatenate([np.full(len(v['f']),v['w'],dtype=np.int64) for v in sel])
        kk = fine_keys(ff,zcut,scut)
        banks[b] = dict(f=ff,phi=pp,w=ww,key=kk)
    keysets = [{tuple(k) for k in banks[b]['key']} for b in train_banks]
    q = keysets[0].intersection(keysets[1])
    assert q
    aggregates = {}
    for b,x in banks.items():
        keep = np.fromiter((tuple(k) in q for k in x['key']),bool,len(x['key']))
        x['keep'] = keep
    # Independently group via numpy unique and weighted bincount/add.at.
    def aggregate(xx, fine):
        keys = np.concatenate([x['key'][x['keep']] for x in xx])
        if not fine:
            keys = keys.copy(); keys[:,2]=-1
        ww = np.concatenate([x['w'][x['keep']] for x in xx])
        pp = np.concatenate([x['phi'][x['keep']] for x in xx])
        unique,inverse = np.unique(keys,axis=0,return_inverse=True)
        counts = np.zeros(len(unique),np.int64); np.add.at(counts,inverse,ww)
        sums = np.zeros((len(unique),10),np.float64)
        np.add.at(sums,inverse,pp*ww[:,None])
        return {tuple(k):dict(n=int(n),sum=s,h=s/n) for k,n,s in zip(unique,counts,sums)}
    aggregates['U'] = aggregate([banks[b] for b in train_banks],False)
    aggregates['S'] = aggregate([banks[b] for b in train_banks],True)
    for b in train_banks:
        aggregates['C_'+b.split('_')[0]] = aggregate([banks[b]],False)
    return dict(zcut=zcut,scut=scut,Q=q,banks=banks,kernels=aggregates)

def expected_test_rows(frames,meta,fold,test_bank,all_branches=False):
    out = []
    tau = float(np.float32(.1))
    descriptions = [e for e in meta['frames'] if e['bank'] == test_bank]
    for e in descriptions:
        v = frames[(test_bank,e['frame'])]
        keys = fine_keys(v['f'],fold['zcut'],fold['scut'])
        keep = np.fromiter((tuple(k) in fold['Q'] for k in keys),bool,len(keys))
        fine_unique,fine_inverse,fine_counts = np.unique(keys[keep],axis=0,return_inverse=True,return_counts=True)
        xy = keys[keep].copy(); xy[:,2]=-1
        coarse_unique,coarse_counts = np.unique(xy,axis=0,return_counts=True)
        # Empty Q response remains a valid diagnostic point.
        for anchor in e['native_query_checks']:
            query = anchor['query_id']
            if not all_branches and not query.endswith('_v0'):
                continue
            block = int(query.split('_')[1][1:]); branch=int(query.split('_')[2][1:]); pose=integer(anchor['pose_index'])
            raw_full = float(np.sum(v['phi'][:,pose],dtype=np.float64))
            raw_q = float(np.sum(v['phi'][keep,pose],dtype=np.float64))
            raw_tail = float(np.sum(v['phi'][~keep,pose],dtype=np.float64))
            close(raw_q+raw_tail,raw_full,'native Q+tail closure')
            prediction={}
            for arm in ('U','S','C_C7','C_K2'):
                kk,cc=(fine_unique,fine_counts) if arm == 'S' else (coarse_unique,coarse_counts)
                predicted_q=math.fsum(int(n)*float(fold['kernels'][arm][tuple(k)]['h'][pose]) for k,n in zip(kk,cc))
                prediction[arm]=dict(q=predicted_q,full=raw_tail+predicted_q,event=int(raw_tail+predicted_q>tau),error=raw_tail+predicted_q-raw_full)
            maskhash=hashlib.sha256(np.packbits(keep,bitorder='little').tobytes()).hexdigest()
            out.append(dict(bank=test_bank,block=block,branch=branch,pose=pose,frame=e['frame'],N=len(keys),N_Q=int(np.sum(keep)),N_tail=int(np.sum(~keep)),maskhash=maskhash,
                            full=raw_full,Q=raw_q,tail=raw_tail,native=float(v['native'][pose]),native_event=int(float(v['native'][pose])>tau),
                            full64_event=int(raw_full>tau),tail_event=int(raw_tail>tau),predictions=prediction))
    assert len(out)==(51 if all_branches else 50), test_bank
    assert sorted(r['block'] for r in out if r['branch']==0)==list(range(50)), test_bank
    return sorted(out,key=lambda r:(r['block'],r['branch']))

def expected_receiver_metrics(rr,arm):
    errors=np.array([r['predictions'][arm]['error'] for r in rr],np.float64)
    assert len(rr)==50
    return dict(MSE=float(np.mean(errors**2)),mean_signed_error=float(np.mean(errors)),MAE=float(np.mean(np.abs(errors))),
                event_errors=sum(r['predictions'][arm]['event']!=r['native_event'] for r in rr),
                Q_particle_exposures=sum(r['N_Q'] for r in rr),tail_particle_exposures=sum(r['N_tail'] for r in rr),
                Q_response_sum=math.fsum(r['Q'] for r in rr),tail_response_sum=math.fsum(r['tail'] for r in rr),
                tail_alone_positive=sum(r['tail_event'] for r in rr))

def independent_fine_moments(frames,banks,fold):
    answer={}
    for bank in banks:
        selected=[v for (b,_),v in frames.items() if b==bank]
        keys=np.concatenate([fine_keys(v['f'],fold['zcut'],fold['scut']) for v in selected])
        phi=np.concatenate([v['phi'] for v in selected]).astype(np.float64)
        w=np.concatenate([np.full(len(v['f']),v['w'],np.int64) for v in selected])
        keep=np.fromiter((tuple(k) in fold['Q'] for k in keys),bool,len(keys))
        kk,inv=np.unique(keys[keep],axis=0,return_inverse=True)
        count=np.zeros(len(kk),np.int64);np.add.at(count,inv,w[keep])
        sums=np.zeros((len(kk),10),np.float64);np.add.at(sums,inv,phi[keep]*w[keep,None])
        answer[bank]={tuple(k):dict(n=int(n),h=s/n) for k,n,s in zip(kk,count,sums)}
    return answer

def verify(rk1,parent):
    rk1=Path(rk1);parent=Path(parent)
    contract=read_json(rk1/'contract.json')
    assert sha(rk1/'contract.json')==(rk1/'PRE_RUN_CONTRACT_SHA256.txt').read_text().split()[0]
    for name,hh in contract['executed_source_SHA256'].items():
        assert sha(rk1/'source'/name)==hh, f'producer source changed: {name}'
    assert sha(rk1/'AUTHORIZED_PLAN_zh.md')==contract['authorized_plan_SHA256']
    for name,hh in contract['input_SHA256'].items():
        assert sha(parent/name)==hh, f'parent input changed: {name}'
    frozen=read_json(rk1/'PRE_ANALYSIS_PREDICTION_SHA256.json')
    for name,hh in frozen.items():
        assert sha(rk1/name)==hh, f'prediction changed after freeze: {name}'
    assert 'PREDICTIONS_BLIND.csv' in frozen
    expected_blind_csv={'NATIVE_ANCHOR_RECHECK.csv','COMMON_SUPPORT_FINE_KEYS.csv','PREDICTIONS_BLIND.csv','CLASS_CONDITIONAL_RESPONSE_DIFFERENCES.csv','MODEL_COMPLEXITY.csv'}
    expected_blind_csv.update(f'{f}_KERNEL_{a}.csv' for f in ('T0_E1','T1_E0') for a in ('U','S','C_C7','C_K2'))
    assert set(frozen)==expected_blind_csv
    cache=parent/'RK0_NEW/reference_contribution_cache'
    meta,frames=load_cache(cache)
    assert all(sum(v['w'] for (b,_),v in frames.items() if b==bank)==50 for bank in meta['reference_ids'])
    nativeledger=read_csv(rk1/'NATIVE_ANCHOR_RECHECK.csv')
    anchors={(e['bank'],q['query_id']):q for e in meta['frames'] for q in e['native_query_checks']}
    assert len(nativeledger)==len(anchors)==204
    for r in nativeledger:
        q=anchors[(r['bank'],r['query_id'])]
        assert integer(r['frame'])==q['frame'] and integer(r['pose_id'])==q['pose_index']
        close(r['cached_native_F32_ppm'],q['native_cpp_ppm'],'native anchor',atol=0,rtol=0)
        close(r['native_CPP_ppm'],q['native_cpp_ppm'],'native anchor',atol=0,rtol=0)
        assert float(r['absolute_difference'])==0
    source_map_path=rk1/'ANALYSIS_ONLY_GENERATOR_MAPPING_FROZEN.json'
    # The map is read only after blind artifact integrity has been checked.
    truthmap=read_json(source_map_path)
    assert read_json(rk1/'POST_FREEZE_GENERATOR_MAPPING.json')==truthmap
    assert truthmap=={b:b.split('_')[0] for b in meta['reference_ids']}
    pred=read_csv(rk1/'PREDICTIONS_BLIND.csv')
    assert len(pred)==408
    lookup={(r['fold'],r['role'],r['bank'],integer(r['block_id']),integer(r['membership_branch'])):r for r in pred}
    assert len(lookup)==408
    actual_meta=read_json(rk1/'FIT_METADATA.json')
    assert {r['fold'] for r in actual_meta}=={'T0_E1','T1_E0'}
    actual_meta={r['fold']:r for r in actual_meta}
    support=read_csv(rk1/'COMMON_SUPPORT_FINE_KEYS.csv')
    cond=read_csv(rk1/'CLASS_CONDITIONAL_RESPONSE_DIFFERENCES.csv')
    condlookup={(r['fold'],integer(r['cell_i']),integer(r['cell_j']),integer(r['class_id']),integer(r['pose_id'])):r for r in cond}
    assert len(condlookup)==len(cond)
    models=('U','S','C_C7','C_K2')
    metrics=[];expected_predictions=[];foldreports=[];condreports=[];maxkernel=0.;maxpred=0.
    for side in (0,1):
        name=f'T{side}_E{1-side}';train=(f'C7_{side}',f'K2_{side}');test=(f'C7_{1-side}',f'K2_{1-side}')
        fold=independent_fold(frames,train)
        fm=actual_meta[name]
        assert fm==read_json(rk1/(name+'_FIT_METADATA.json'))
        close(fm['z_split_m'],fold['zcut'],'train-only z median',atol=0,rtol=0)
        close(fm['sigma_split_cm'],fold['scut'],'train-only sigma median',atol=0,rtol=0)
        assert fm['train_banks']==list(train) and fm['test_banks']==list(test)
        qq={tuple(integer(r[c]) for c in ('cell_i','cell_j','class_id')) for r in support if r['fold']==name}
        assert qq==fold['Q'] and len(qq)==fm['common_fine_keys']
        assert len([r for r in support if r['fold']==name])==len(qq)
        denominators={}
        zero_denoms={}
        for arm in models:
            expected=fold['kernels'][arm]
            kr=read_csv(rk1/(name+'_KERNEL_'+arm+'.csv'))
            assert len(kr)==len(expected)*10
            seen=set()
            for r in kr:
                key=tuple(integer(r[c]) for c in ('cell_i','cell_j','class_id'));pose=integer(r['pose_id'])
                assert (key,pose) not in seen;seen.add((key,pose))
                assert r['fold']==name and r['arm']==arm and key in expected and pose in range(10)
                exp=expected[key]
                assert integer(r['particle_exposure_denominator'])==exp['n']
                close(r['phi_sum_ppm'],exp['sum'][pose],f'{name} {arm} numerator')
                close(r['h_ppm_per_particle'],exp['h'][pose],f'{name} {arm} h')
                maxkernel=max(maxkernel,abs(float(r['h_ppm_per_particle'])-float(exp['h'][pose])))
            denominators[arm]=sum(x['n'] for x in expected.values())
            assert fm['eligible_particle_exposure_denominators'][arm]==denominators[arm]
            assert fm['active_cell_classes'][arm]==len(expected)
        assert denominators['U']==denominators['S']==denominators['C_C7']+denominators['C_K2']
        for b in train:
            x=fold['banks'][b]
            keep=x['keep']
            zero_denoms[b]=int(np.sum(x['w'][keep]*(np.all(x['phi'][keep]==0,axis=1))))
            assert fm['all_training_exposures'][b]==int(np.sum(x['w']))
        moments=independent_fine_moments(frames,train+test,fold)
        active=0;samesign=0;opposite=0;testnear0=0;supported=0;weighted_error=0.;weightdenom=0
        for key in fold['Q']:
            for pose in range(10):
                r=condlookup[(name,)+key+(pose,)]
                assert r['not_fit_input'].lower()=='true'
                hh={};nn={}
                for role,banks in (('train',train),('test',test)):
                    for src,bank in zip(('C7','K2'),banks):
                        xx=moments[bank].get(key);n=xx['n'] if xx else 0
                        assert integer(r[role+'_'+src+'_count'])==n
                        nn[(role,src)]=n
                        if n:
                            h=float(xx['h'][pose]);hh[(role,src)]=h
                            close(r[role+'_'+src+'_h'],h,f'conditional {role} h')
                        else:
                            assert r[role+'_'+src+'_h']=='UNSUPPORTED'
                    if nn[(role,'C7')] and nn[(role,'K2')]:
                        delta=hh[(role,'C7')]-hh[(role,'K2')]
                        close(r[role+'_C7_minus_K2_h'],delta,'conditional difference')
                        hh[(role,'difference')]=delta
                    else:
                        assert r[role+'_C7_minus_K2_h']=='UNSUPPORTED'
                if nn[('test','C7')] and nn[('test','K2')]:
                    supported+=1;ww=min(nn[('test','C7')],nn[('test','K2')]);weightdenom+=ww
                    tr=hh[('train','difference')];te=hh[('test','difference')]
                    weighted_error+=ww*(tr-te)**2
                    if abs(tr)>3e-13:
                        active+=1
                        if abs(te)<=3e-13:testnear0+=1
                        elif tr*te>0:samesign+=1
                        else:opposite+=1
        condreports.append(dict(fold=name,train_common_key_pose_rows=len(fold['Q'])*10,test_both_source_supported_rows=supported,
                                nonzero_training_difference_rows=active,same_sign_test_rows=samesign,opposite_sign_test_rows=opposite,
                                test_nearzero_among_active=testnear0,weighted_difference_MSE=weighted_error/weightdenom))
        for role,banks in (('train',train),('test',test)):
            for bank in banks:
                erows=expected_test_rows(frames,meta,fold,bank,all_branches=True)
                for e in erows:
                    r=lookup[(name,role,bank,e['block'],e['branch'])]
                    for col,val in [('frame',e['frame']),('pose_id',e['pose']),('total_particles',e['N']),('eligible_particles',e['N_Q']),('tail_particles',e['N_tail']),
                                    ('target_phi64_event',e['full64_event']),('native_F32_event',e['native_event']),('tail_alone_event',e['tail_event'])]:
                        assert integer(r[col])==val,(name,bank,e['block'],col)
                    assert r['eligible_mask_SHA256']==e['maskhash']
                    for col,val in [('target_Q64_ppm',e['Q']),('tail_Qoutside64_ppm',e['tail']),('target_phi64_ppm',e['full']),('native_full_F32_ppm',e['native']),('phi64_minus_native_F32_ppm',e['full']-e['native'])]:
                        close(r[col],val,'Q-tail-native target '+col)
                    near=abs(e['full']-float(np.float32(.1)))<=3e-7+5e-6*abs(e['full'])
                    assert (r['full_target_near_threshold'].lower()=='true')==near
                    for arm in models:
                        pp=e['predictions'][arm]
                        close(r[arm+'_Q_prediction_ppm'],pp['q'],'arm Q prediction')
                        close(r[arm+'_prediction_ppm'],pp['full'],'arm full prediction')
                        assert integer(r[arm+'_event'])==pp['event']
                        assert integer(r[arm+'_changed_event_vs_tail'])==int(pp['event']!=e['tail_event'])
                        # Same actual tail exactly cancels in continuous prediction error.
                        close(float(r[arm+'_prediction_ppm'])-float(r['target_phi64_ppm']),float(r[arm+'_Q_prediction_ppm'])-float(r['target_Q64_ppm']),'tail cancellation')
                        maxpred=max(maxpred,abs(float(r[arm+'_prediction_ppm'])-pp['full']))
                    e.update(fold=name,role=role)
                    expected_predictions.append(e)
                main=[r for r in erows if r['branch']==0]
                for arm in models+('C_ORACLE',):
                    selected='C_'+truthmap[bank] if arm=='C_ORACLE' else arm
                    mm=expected_receiver_metrics(main,selected)
                    metrics.append(dict(fold=name,role=role,bank=bank,arm=arm,selected=selected,**mm))
        foldreports.append(dict(fold=name,z_split_m=fold['zcut'],sigma_split_cm=fold['scut'],common_fine_keys=len(fold['Q']),eligible_denominators=denominators,
                                entirely_zero_across_10poses_training_particle_exposures=zero_denoms))
    assert len(expected_predictions)==408 and len(metrics)==40
    assert len(cond)==sum(x['common_fine_keys']*10 for x in foldreports)
    actualmetrics=read_csv(rk1/'BANK_METRICS_ANALYSIS.csv')
    assert len(actualmetrics)==40
    mmlookup={(r['fold'],r['role'],r['bank'],r['arm']):r for r in actualmetrics}
    for m in metrics:
        r=mmlookup[(m['fold'],m['role'],m['bank'],m['arm'])]
        assert r['generating_condition_analysis_only']==truthmap[m['bank']]
        assert r['C_selected_analysis_only']==(m['selected'] if m['arm']=='C_ORACLE' else '')
        assert integer(r['planned_exposures'])==50 and integer(r['independent_realizations'])==1
        for col,expected in [('MSE_ppm2',m['MSE']),('mean_signed_error_ppm',m['mean_signed_error']),('MAE_ppm',m['MAE']),
                             ('eligible_response_fraction',m['Q_response_sum']/(m['Q_response_sum']+m['tail_response_sum']))]:
            close(r[col],expected,'bank metric '+col)
        assert integer(r['event_errors_native_F32'])==m['event_errors']
        rr=[x for x in expected_predictions if (x['fold'],x['role'],x['bank'],x['branch'])==(m['fold'],m['role'],m['bank'],0)]
        assert integer(r['event_errors_phi64'])==sum(x['predictions'][m['selected']]['event']!=x['full64_event'] for x in rr)
        assert integer(r['tail_alone_positive_events'])==m['tail_alone_positive']
    cs=read_json(rk1/'CONDITIONAL_DIFFERENCE_SUMMARY.json')
    cs={r['fold']:r for r in cs}
    for expected in condreports:
        for k,v in expected.items():
            if k=='fold':continue
            if k=='weighted_difference_MSE':close(cs[expected['fold']][k],v,k)
            else:assert cs[expected['fold']][k]==v,k
    paired=read_csv(rk1/'TEST_BANK_PAIRED_COMPARISONS.csv')
    assert len(paired)==4
    mindex={(r['fold'],r['role'],r['bank'],r['arm']):r for r in metrics}
    checked_pairs=[]
    for p in paired:
        u,s,c=[mindex[(p['fold'],'test',p['bank'],a)]['MSE'] for a in ('U','S','C_ORACLE')]
        tol=max(1e-12,1e-10*max(u,s,c))
        expected=dict(U_MSE_ppm2=u,S_MSE_ppm2=s,C_ORACLE_MSE_ppm2=c,U_to_S_MSE_reduction=u-s,S_to_C_MSE_reduction=s-c,U_to_C_MSE_reduction=u-c,
                      U_to_S_relative_reduction=(u-s)/u,S_to_C_relative_reduction=(s-c)/s,comparison_tolerance_ppm2=tol)
        for k,v in expected.items():close(p[k],v,'paired '+k)
        bools=dict(S_better_than_U=u-s>tol,C_better_than_S=s-c>tol,C_better_than_U=u-c>tol)
        for k,v in bools.items():assert (p[k].lower()=='true')==v,k
        checked_pairs.append(dict(fold=p['fold'],bank=p['bank'],**expected,**bools))
    result=read_json(rk1/'RK1_RESULT.json')
    assert result['test_banks']==4 and result['test_exposures']==200
    assert all(result[k]==0 for k in ('independent_new_realizations','new_phi_calls','new_simulation','new_network_training'))
    assert result['kernel_tables_fitted']==8
    assert result['arms']==list(models)
    for key,flag in [('S_MSE_gains','S_better_than_U'),('C_oracle_over_S_MSE_gains','C_better_than_S'),('C_oracle_over_U_MSE_gains','C_better_than_U')]:
        assert result[key]==sum(x[flag] for x in checked_pairs)
    for arm in models+('C_ORACLE',):
        close(result['equal_bank_mean_test_MSE'][arm],math.fsum(m['MSE'] for m in metrics if m['role']=='test' and m['arm']==arm)/4,'equal bank aggregate')
    assert result['all_four_S_improve']==all(x['S_better_than_U'] for x in checked_pairs)
    assert result['all_four_C_over_S_improve']==all(x['C_better_than_S'] for x in checked_pairs)
    for src in ('C7','K2'):
        x=[p for p in checked_pairs if truthmap[p['bank']]==src]
        assert result['per_source_directions'][src]['S_over_U']==[p['S_better_than_U'] for p in x]
        assert result['per_source_directions'][src]['C_over_S']==[p['C_better_than_S'] for p in x]
    complexity=read_csv(rk1/'MODEL_COMPLEXITY.csv')
    assert len(complexity)==8
    for r in complexity:
        f=actual_meta[r['fold']];a=r['arm']
        assert integer(r['active_keys'])==f['active_cell_classes'][a]
        assert integer(r['receiver_coefficients'])==10*integer(r['active_keys'])
        assert integer(r['particle_exposure_denominator'])==f['eligible_particle_exposure_denominators'][a]
    ledger=read_json(rk1/'EXECUTION_LEDGER.json')
    assert ledger['contract_SHA256']==sha(rk1/'contract.json')
    assert ledger['status']=='PASS_COMPLETED_ONE_ARITHMETIC_BATCH' and ledger['batch_entry_count']==1
    assert ledger['exitcode']==0 and ledger['resource_stop'] is None and ledger['own_child_running'] is False
    assert ledger['wall_s']<=300 and ledger['peak_RSS_bytes']<=512*1024**2 and ledger['peak_output_bytes']<=200*1024**2
    assert all(ledger[x]==0 for x in ('new_phi_queries','new_GADEN','new_CFD','new_ROS','new_VM','new_navigation','new_network_training'))
    assert ledger['kernel_tables_fitted']==8 and ledger['native_input_files_modified'] is False
    checked=dict(status='PASS_INDEPENDENT_CACHE_ONLY_RECOMPUTATION',input_hashes=len(contract['input_SHA256']),executed_source_hashes=len(contract['executed_source_SHA256']),
                 pre_analysis_artifact_hashes=len(frozen),old_cache_files=196,native_serial_F32_CPP_anchors=204,kernel_tables=8,
                 blind_wide_rows=408,test_main_exposures=200,test_arm_exposures=800,all_wide_arm_values=408*4,bank_metrics=40,
                 conditional_fine_key_pose_rows=len(cond),maximum_h_absolute_difference=maxkernel,maximum_prediction_absolute_difference=maxpred,
                 folded_support_and_zero_denominators_checked=foldreports,source_map_selected_only_after_blind_hash_verification=True,
                 new_phi_or_producer_calls=0,science_scope='Cache-only verification, same-tail oracle, no new localization/classification result.')
    return checked,dict(independent_bank_metrics=metrics,independent_test_pairs=checked_pairs,independent_conditional_summaries=condreports)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--rk1',type=Path,required=True)
    p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--outdir',type=Path)
    a=p.parse_args();r,t=verify(a.rk1,a.parent)
    if a.outdir:
        a.outdir.mkdir(parents=True,exist_ok=True)
        for n,v in [('INDEPENDENT_VERIFY_RESULT.json',r),('INDEPENDENT_VERIFY_TABLES.json',t)]:
            (a.outdir/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
