"""Independent post-score public-kernel and exported arithmetic audit."""
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import numpy as np
import torch
from verify_implementation import extract

ROOT=Path(__file__).resolve().parents[3]
E=ROOT/'evidence/ocb_r2/r2c_signature_path'


def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))


def main():
    scope={'np':np,'torch':torch}
    extract('static_kernels.py',['RBFKernel'],scope)
    extract('sigkernel.py',['tile','SigKernel_naive'],scope)
    index=rows(E/'R2C_INPUTS_INDEX.tsv')
    paths={}
    for r in index:
        b=np.load(ROOT/f"evidence/ocb_r2/mechanism_census_r0/inputs/{r['run_id']}.pooled.npy")>0
        paths[r['run_id']]=np.vstack((np.zeros((1,31)),np.column_stack((np.arange(10)/9,b/np.sqrt(30)))))
    sets={c:sorted([r for r in index if r['context']==c],key=lambda r:(r['source'],int(r['replica']))) for c in sorted({r['context'] for r in index})}
    pairs=[(a['run_id'],b['run_id']) for seq in sets.values() for a in seq for b in seq]
    x=torch.tensor([paths[a].tolist() for a,b in pairs],dtype=torch.float64)
    y=torch.tensor([paths[b].tolist() for a,b in pairs],dtype=torch.float64)
    ks=scope['SigKernel_naive'](x,y,scope['RBFKernel'](1),dyadic_order=1).tolist()
    gram=dict(zip(pairs,ks))
    exported=rows(E/'R2C_CANDIDATES.tsv');maxraw=0.;maxarithmetic=0.
    for r in exported:
        ref=[u['run_id'] for u in sets[r['context']] if u['source']==r['candidate_source'] and int(u['replica'])!=int(r['candidate_omitted_replicate'])]
        independent=sum(gram[a,b] for a in ref for b in ref if a!=b)/6-2*sum(gram[a,r['run_id']] for a in ref)/3
        maxraw=max(maxraw,abs(independent-float(r['SIG_RAW'])))
        q=float(r['Q_self_mean'])-2*float(r['Q_target_mean'])
        maxarithmetic=max(maxarithmetic,abs(q-float(r['SIG_Q'])),abs(q-independent-float(r['D_SIG'])))
    assert maxraw<1e-10 and maxarithmetic<1e-10
    # Frozen six Q draws: generic upstream path kernel checks both terms.
    chosen=exported[0];seq=sets[chosen['context']]
    ref=[paths[u['run_id']] for u in seq if u['source']==chosen['candidate_source'] and int(u['replica'])!=int(chosen['candidate_omitted_replicate'])]
    bank=np.stack(ref).transpose(1,0,2)
    ci=int(chosen['context'][1:]);si=sorted({u['source'] for u in seq}).index(chosen['candidate_source'])
    key=[2026093201,ci,si,int(chosen['target_replicate']),int(chosen['alternative_omission'])]
    choices=[]
    for ch in (0,1,2):
        rr=np.random.default_rng(np.random.SeedSequence([*key,ch])).integers(0,3,size=(4096,10),dtype=np.int64)
        choices.append(np.column_stack((np.zeros(4096,dtype=np.int64),rr)))
    generic_q=[bank[np.arange(11),a] for a in choices[0]]
    qa=[bank[np.arange(11),a] for a in choices[1]]
    qb=[bank[np.arange(11),a] for a in choices[2]]
    qtx=torch.tensor([p.tolist() for p in generic_q+qa],dtype=torch.float64)
    qty=torch.tensor([paths[chosen['run_id']].tolist()]*4096+[p.tolist() for p in qb],dtype=torch.float64)
    qk=np.array(scope['SigKernel_naive'](qtx,qty,scope['RBFKernel'](1),dyadic_order=1).tolist())
    matching=[r for r in exported if r['run_id']==chosen['run_id'] and r['candidate_source']==chosen['candidate_source'] and r['alternative_omission']==chosen['alternative_omission']]
    qerror=0.
    for r in matching:
        b=int(r['B']);value=float(qk[4096:4096+b].mean()-2*qk[:b].mean())
        qerror=max(qerror,abs(value-float(r['SIG_Q'])))
    assert qerror<1e-10
    targets=rows(E/'R2C_TARGETS.tsv');primary=[r for r in targets if r['primary_omission']=='1']
    positives=sum(float(r['Delta_SIG'])>0 for r in primary)
    rescue=sum(float(r['Delta_SIG'])>0 and float(r['Delta_ES'])<=0 for r in primary)
    harm=sum(float(r['Delta_SIG'])<=0 and float(r['Delta_ES'])>0 for r in primary)
    cmeans=[statistics.mean(float(r['Delta_SIG']) for r in primary if r['context']==c) for c in sets]
    observed=statistics.mean(cmeans)
    p=sum(statistics.mean(a*b for a,b in zip(cmeans,s))>=observed-1e-15 for s in itertools.product((-1,1),repeat=8))/256
    result=json.loads((E/'R2C_RESULT.json').read_text())
    assert (positives,rescue,harm)==(result['SIG_correct'],result['rescues'],result['harms'])
    assert p==result['summary']['exact_signflip']
    anatomical=rows(E/'R2C_SIGNATURE_LEVEL_ANATOMY.tsv')
    level1=[float(r['Delta']) for r in anatomical if r['level']=='LEVEL1' and r['primary_omission']=='1']
    # Level1 is the endpoint feature: RAW and Q have identical endpoint laws.
    # The prescribed U-versus-empirical-product self terms leave a finite-K bias.
    level1_bias_error=0.
    for row in [r for r in anatomical if r['level']=='LEVEL1']:
        target=next(r for r in targets if r['run_id']==row['run_id'] and r['alternative_omitted_replicate']==row['alternative_omitted_replicate'])
        values=[]
        for source,omitted in ((target['truth_source'],int(target['target_replicate'])),
                               (target['alternative_source'],int(target['alternative_omitted_replicate']))):
            endpoints=np.stack([paths[u['run_id']][-1] for u in sets[row['context']] if u['source']==source and int(u['replica'])!=omitted])
            values.append(float(np.square(endpoints-endpoints.mean(axis=0)).sum()/6))
        level1_bias_error=max(level1_bias_error,abs(values[0]-float(row['D_truth'])),
            abs(values[1]-float(row['D_alt'])),abs(values[0]-values[1]-float(row['Delta'])))
    assert level1_bias_error<1e-10
    # Sign counts of rounding-scale zero entries are not source evidence.
    zero_within_tolerance=sum(abs(d)<=1e-10 for d in level1)
    repeat=json.loads((E/'R2C_REPEAT.json').read_text())
    assert repeat['byte_identical']
    for name,digest in repeat['files_sha256'].items():
        assert hashlib.sha256((E/name).read_bytes()).hexdigest()==digest
        assert (E/'pass1'/name).read_bytes()==(E/'pass2'/name).read_bytes()
    audit=dict(decision='R2C_INDEPENDENT_AUDIT_PASS',independent_public_kernel_pairs=512,
        all_exported_candidate_RAW_scores_checked=len(exported),max_RAW_error=maxraw,max_score_arithmetic_error=maxarithmetic,
        independent_Q_kernel_pairs=8192,Q_2048_and_4096_one_fixed_candidate_max_error=qerror,
        independent_target_correct=positives,rescues=rescue,harms=harm,exact_signflip=p,
        level1_primary_zero_within_frozen_tolerance=zero_within_tolerance,level1_max_abs_delta=max(abs(d) for d in level1),
        level1_finite_K_self_term_identity_max_error=level1_bias_error,
        level1_residual_is_endpoint_spread_estimator_difference_not_temporal_coupling=True,
        raw_strict_sign_counts_retained_but_level1_roundoff_not_interpreted=True,repeat_all_hashes_verified=True)
    (E/'R2C_INDEPENDENT_AUDIT.json').write_bytes((json.dumps(audit,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps(audit,sort_keys=True,indent=2))


if __name__=='__main__':main()
