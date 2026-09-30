"""Frozen R2C execution: input parity, all omissions, Q convergence, exact repeat."""
import itertools
import json
import math
from pathlib import Path
import shutil
import sys
import time
import numpy as np
import signature_core as sc

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/ocb_r2/r2b_dependence_score'))
import run_r2b as common
r0=common.r0
OUT=ROOT/'evidence/ocb_r2/r2c_signature_path'
HERE=Path(__file__).resolve().parent


def input_parity():
    runs,contexts,tensors,comparator,old=common.input_parity()
    implementation=json.loads((OUT/'R2C_IMPLEMENTATION_PARITY.json').read_text())
    assert implementation['decision']=='R2C_IMPLEMENTATION_PARITY_PASS'
    for name,digest in implementation['source_sha256'].items():
        assert common.sha(HERE/'upstream_reference'/name)==digest
    old.update(decision='R2C_INPUT_PARITY_PASS',
        scorer_sha256=common.sha(__file__),core_sha256=common.sha(HERE/'signature_core.py'),
        protocol_sha256=common.sha(ROOT/'research/ocb_r2/R2C_SIGNATURE_PATH_PROTOCOL_20260930.md'),
        freeze_sha256=common.sha(HERE/'R2C_PROTOCOL_FROZEN.md'),
        reused_parity_helper_sha256=common.sha(Path(common.__file__)),
        implementation_parity_sha256=common.sha(OUT/'R2C_IMPLEMENTATION_PARITY.json'))
    return runs,contexts,tensors,comparator,old


def calculate(runs,contexts,tensors,comparator):
    banks=r0.references(runs,tensors,contexts)
    lookup={(r['context'],r['source'],r['replica']):r for r in runs}
    baseline={(r['run_id'],int(r['alternative_omitted_replicate'])):r for r in comparator}
    records=[];candidate_rows=[];anatomy=[]
    for ci,c in enumerate(contexts):
        sources=(c['source_a'],c['source_b'])
        for truth_idx,truth in enumerate(sources):
            for rep in range(1,5):
                run=lookup[(c['context'],truth,rep)]
                y=banks[(c['context'],truth_idx)][rep-1]
                for altomit in range(1,5):
                    computed=[]
                    for si,candidate in enumerate(sources):
                        omit=rep if si==truth_idx else altomit
                        ref=np.delete(banks[(c['context'],si)],omit-1,axis=0)
                        raw=sc.raw_score(ref,y)
                        q=sc.q_scores(ref,y,[ci,si,rep,altomit])
                        levels=sc.anatomy_scores(ref,y)
                        computed.append((raw,q,levels))
                        for b in (2048,4096):
                            candidate_rows.append(dict(run_id=run['run_id'],context=c['context'],candidate_source=candidate,
                                target_replicate=rep,alternative_omission=altomit,candidate_omitted_replicate=omit,
                                candidate_role='TRUTH' if si==truth_idx else 'ALTERNATIVE',B=b,
                                SIG_RAW=raw,**q[b],D_SIG=q[b]['SIG_Q']-raw,
                                seed_key=f'2026093201,{ci},{si},{rep},{altomit},channel0/1/2'))
                    tr,tq,tl=computed[truth_idx];ar,aq,al=computed[1-truth_idx]
                    old=baseline[(run['run_id'],altomit)]
                    delta=tq[2048]['SIG_Q']-tr-aq[2048]['SIG_Q']+ar
                    audit=tq[4096]['SIG_Q']-tr-aq[4096]['SIG_Q']+ar
                    records.append(dict(context=c['context'],house=c['house'],wind=c['wind'],gas=c['gas'],
                        run_id=run['run_id'],truth_source=truth,alternative_source=sources[1-truth_idx],
                        target_replicate=rep,alternative_omitted_replicate=altomit,primary_omission=int(rep==altomit),
                        SIG_RAW_truth=tr,SIG_Q_truth=tq[2048]['SIG_Q'],D_SIG_truth=tq[2048]['SIG_Q']-tr,
                        SIG_RAW_alt=ar,SIG_Q_alt=aq[2048]['SIG_Q'],D_SIG_alt=aq[2048]['SIG_Q']-ar,
                        Delta_SIG=delta,Delta_SIG_4096=audit,G_SIG_RAW=ar-tr,
                        Delta_ES=float(old['Delta_BM']),SIG_correct=int(delta>0),ES_correct=int(float(old['Delta_BM'])>0)))
                    for i,level in enumerate(('LEVEL1','LE2','LE3')):
                        anatomy.append(dict(run_id=run['run_id'],context=c['context'],house=c['house'],truth_source=truth,
                            target_replicate=rep,alternative_omitted_replicate=altomit,primary_omission=int(rep==altomit),
                            level=level,D_truth=tl[i],D_alt=al[i],Delta=tl[i]-al[i],correct=int(tl[i]>al[i]),Q_integration='EXACT',
                            feature_map='LINEAR_R31_CHEN_DISTINCT_FROM_PRIMARY_RBF'))
        print(f"scored {c['context']} ({ci+1}/8)",flush=True)
    assert len(records)==256 and len(candidate_rows)==1024 and len(anatomy)==768
    return records,candidate_rows,anatomy


def groups_for(records,contexts):
    result=[]
    for c in contexts:
        for s in (c['source_a'],c['source_b']):
            sub=[r for r in records if r['context']==c['context'] and r['truth_source']==s]
            assert len(sub)==4
            result.append(dict(context=c['context'],house=c['house'],wind=c['wind'],gas=c['gas'],truth_source=s,
                SIG_correct=sum(r['SIG_correct'] for r in sub),ES_correct=sum(r['ES_correct'] for r in sub),
                mean_Delta_SIG=common.mean([r['Delta_SIG'] for r in sub]),mean_Delta_ES=common.mean([r['Delta_ES'] for r in sub])))
    return result


def aggregate(records,contexts,anatomy):
    p=[r for r in records if r['primary_omission']]
    groups=groups_for(p,contexts);summary=common.summarize(groups,'mean_Delta_SIG')
    ctx=[]
    for c in contexts:
        sub=[r for r in p if r['context']==c['context']]
        ctx.append(dict(context=c['context'],house=c['house'],wind=c['wind'],gas=c['gas'],
            SIG_correct=sum(r['SIG_correct'] for r in sub),ES_correct=sum(r['ES_correct'] for r in sub),
            mean_Delta_SIG=common.mean([r['Delta_SIG'] for r in sub])))
    omissions=[]
    for o in range(1,5):
        sub=[r for r in records if r['alternative_omitted_replicate']==o]
        s=common.summarize(groups_for(sub,contexts),'mean_Delta_SIG')
        omissions.append(dict(alternative_omission=o,SIG_correct=sum(r['SIG_correct'] for r in sub),
            House01_group_median=s['house_medians']['House01'],House02_group_median=s['house_medians']['House02'],
            pooled_group_median=s['pooled_group_median'],positive_groups=s['positive_groups'],positive_contexts=s['positive_contexts']))
    paired=[dict(run_id=r['run_id'],context=r['context'],house=r['house'],truth_source=r['truth_source'],
        Delta_ES=r['Delta_ES'],Delta_SIG=r['Delta_SIG'],ES_correct=r['ES_correct'],SIG_correct=r['SIG_correct'],
        outcome='RESCUE' if r['SIG_correct'] and not r['ES_correct'] else 'HARM' if r['ES_correct'] and not r['SIG_correct'] else 'UNCHANGED') for r in p]
    rescue=sum(r['outcome']=='RESCUE' for r in paired);harm=sum(r['outcome']=='HARM' for r in paired);n=rescue+harm
    binomial=sum(math.comb(n,k) for k in range(rescue,n+1))/2**n if n else 1.
    houses={h:dict(SIG_correct=sum(r['SIG_correct'] for r in p if r['house']==h),
                   ES_correct=sum(r['ES_correct'] for r in p if r['house']==h),targets=32) for h in ('House01','House02')}
    abs_sum=sum(abs(r['mean_Delta_SIG']) for r in ctx)
    contribution={r['context']:abs(r['mean_Delta_SIG'])/abs_sum if abs_sum else 0 for r in ctx}
    da=np.array([r['Delta_SIG'] for r in p]);db=np.array([r['Delta_SIG_4096'] for r in p])
    median_abs=float(np.median(np.abs(da)));maxchange=float(np.max(np.abs(da-db)))
    signs=int(np.sum((da>0)==(db>0)))
    convergence=dict(B_primary=2048,B_audit=4096,targets=64,sign_agreement=signs,
        median_absolute_primary_delta=median_abs,max_absolute_delta_change=maxchange,
        allowed_maximum_delta_change=.1*median_abs,
        median_numerically_zero=median_abs<=1e-10,pass_signs=signs>=63,pass_change=maxchange<=.1*median_abs,
        all_omission_sign_agreement=sum((r['Delta_SIG']>0)==(r['Delta_SIG_4096']>0) for r in records),
        audit_result_never_selected=True)
    convergence['passed']=convergence['pass_signs'] and convergence['pass_change'] and not convergence['median_numerically_zero']
    conditions=dict(target_positive_ge58=sum(r['SIG_correct'] for r in p)>=58,
        House01_ge26=houses['House01']['SIG_correct']>=26,House02_ge27=houses['House02']['SIG_correct']>=27,
        groups_ge15=summary['positive_groups']>=15,contexts_all8=summary['positive_contexts']==8,
        all_LOCO_positive=all(v>0 for v in summary['leave_one_context_out'].values()),
        signflip_le05=summary['exact_signflip']<=.05,
        all_omission_house_pooled_medians_positive=all(min(r['House01_group_median'],r['House02_group_median'],r['pooled_group_median'])>0 for r in omissions),
        paired_rescue_harm=rescue>harm and binomial<=.05,context_contribution_le40=max(contribution.values())<=.4,
        Q_convergence=convergence['passed'])
    stable=min(summary['house_medians'].values())>0 and summary['positive_groups']>=12 and summary['positive_contexts']>=6 and summary['exact_signflip']<=.05
    result=dict(conditions=conditions,stable=stable,SIG_correct=sum(r['SIG_correct'] for r in p),ES_correct=53,targets=64,
        houses=houses,summary=summary,rescues=rescue,harms=harm,discordant_exact_binomial_p=binomial,
        context_absolute_contribution=contribution,confirmation_and_house03_sealed=True)
    anatomy_summary=[]
    for level in ('LEVEL1','LE2','LE3'):
        for house in ('ALL','House01','House02'):
            sub=[r for r in anatomy if r['primary_omission'] and r['level']==level and (house=='ALL' or r['house']==house)]
            anatomy_summary.append(dict(level=level,house=house,targets=len(sub),positive=sum(r['correct'] for r in sub),
                mean_delta=common.mean([r['Delta'] for r in sub]),median_delta=common.med([r['Delta'] for r in sub])))
    return result,groups,ctx,omissions,paired,convergence,anatomy_summary


def main():
    started=time.monotonic()
    runs,contexts,tensors,comparator,parity=input_parity()
    OUT.mkdir(parents=True,exist_ok=True)
    names=[]
    for passno in (1,2):
        dest=OUT/f'pass{passno}';dest.mkdir(exist_ok=True)
        records,candidates,anatomy=calculate(runs,contexts,tensors,comparator)
        result,groups,ctx,omissions,paired,conv,anat=aggregate(records,contexts,anatomy)
        output={'R2C_TARGETS.tsv':records,'R2C_CANDIDATES.tsv':candidates,'R2C_GROUPS.tsv':groups,
            'R2C_CONTEXTS.tsv':ctx,'R2C_OMISSION.tsv':omissions,'R2C_RESCUE_HARM.tsv':paired,
            'R2C_SIGNATURE_LEVEL_ANATOMY.tsv':anatomy,'R2C_ANATOMY_SUMMARY.tsv':anat,
            'R2C_INPUTS_INDEX.tsv':[{k:r[k] for k in ('run_id','context','house','source','replica','seed')} for r in runs]}
        for name,rows in output.items():r0.write_tsv(dest/name,rows)
        j={'R2C_INPUT_PARITY.json':parity,'R2C_GATES.json':result,'R2C_Q_CONVERGENCE.json':conv}
        for name,obj in j.items():common.write_json(dest/name,obj)
        names=list(output)+list(j)
        print(f'pass {passno} finished',flush=True)
    equal=all((OUT/'pass1'/n).read_bytes()==(OUT/'pass2'/n).read_bytes() for n in names)
    assert equal
    for n in names:shutil.copyfile(OUT/'pass1'/n,OUT/n)
    common.write_json(OUT/'R2C_REPEAT.json',dict(byte_identical=True,full_scoring_passes=2,files_sha256={n:common.sha(OUT/n) for n in names}))
    result['conditions']['deterministic_repeat']=True
    result['decision']=('OCB_R2_R2C_SIGNATURE_PATH_AMPLIFIES' if all(result['conditions'].values()) else
        'OCB_R2_R2C_SIGNATURE_PATH_STABLE_NOT_AMPLIFIED' if result['stable'] else 'OCB_R2_R2C_SIGNATURE_PATH_NO_GO')
    common.write_json(OUT/'R2C_RESULT.json',result)
    common.write_json(OUT/'R2C_RUNTIME.json',dict(wall_seconds=time.monotonic()-started,python=sys.version,numpy=np.__version__,backend='Numba CPU float64; no learned model',full_passes=2))
    print(json.dumps(result,sort_keys=True,indent=2))


if __name__=='__main__':main()
