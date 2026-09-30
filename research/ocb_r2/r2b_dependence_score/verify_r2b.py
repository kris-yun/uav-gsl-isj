#!/usr/bin/env python3
"""Independent integer-arithmetic verification of all R2B primary/omission scores."""
from __future__ import annotations
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'evidence/ocb_r2/r2b_dependence_score'
INPUT = ROOT / 'evidence/ocb_r2/mechanism_census_r0/inputs'


def rows(p):
    with p.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def exact_numerator(ref, y):
    raw_error, q_error = 0, 0
    for lag in (1, 2, 3):
        for t in range(10-lag):
            a, b = ref[:, t, :], ref[:, t+lag, :]
            raw_count = sum((a[i, :, None] != b[i, None, :]).astype(np.int64) for i in range(3))
            q_count = sum((a[i, :, None] != b[j, None, :]).astype(np.int64)
                          for i in range(3) for j in range(3))
            obs = (y[t, :, None] != y[t+lag, None, :]).astype(np.int64)
            raw_error += int(np.square(3*obs - raw_count).sum())
            q_error += int(np.square(9*obs - q_count).sum())
    return q_error-9*raw_error, raw_error, q_error


def main():
    index = rows(OUT/'R2B_INPUTS_INDEX.tsv')
    lookup, tensors = {}, {}
    for r in index:
        p = INPUT / (r['run_id']+'.pooled.npy')
        assert hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256']
        tensors[r['run_id']] = np.load(p, allow_pickle=False)>0
        lookup[(r['context'], r['source'], int(r['replica']))] = r['run_id']
    records = rows(OUT/'R2B_TARGETS.tsv')
    denominator = 81*21600
    mismatched_signs, max_error = [], 0.0
    for r in records:
        y = tensors[r['run_id']]
        nums=[]
        for role, source, omitted in [('truth',r['truth_source'],int(r['target_replicate'])),
                                     ('alt',r['alternative_source'],int(r['alternative_omitted_replicate']))]:
            ref=np.stack([tensors[lookup[(r['context'],source,i)]] for i in range(1,5) if i!=omitted])
            num, re, qe = exact_numerator(ref,y)
            assert abs(float(r[f'VS_RAW_{role}'])-re/(9*21600))<1e-14
            assert abs(float(r[f'VS_Q_{role}'])-qe/(81*21600))<1e-14
            nums.append(num)
        exact_delta=(nums[0]-nums[1])/denominator
        max_error=max(max_error,abs(exact_delta-float(r['Delta_VS'])))
        assert abs(exact_delta-float(r['Delta_VS']))<1e-14
        if (exact_delta>0)!=(float(r['Delta_VS'])>0):
            mismatched_signs.append(dict(run_id=r['run_id'],omission=r['alternative_omitted_replicate'],
                                         exact_delta=exact_delta,export_delta=float(r['Delta_VS'])))
    primary=[r for r in records if r['primary_omission']=='1']
    vs=sum(float(r['Delta_VS'])>0 for r in primary)
    es=sum(float(r['Delta_ES'])>0 for r in primary)
    rescue=sum(float(r['Delta_VS'])>0 and float(r['Delta_ES'])<=0 for r in primary)
    harm=sum(float(r['Delta_VS'])<=0 and float(r['Delta_ES'])>0 for r in primary)
    n=rescue+harm
    paired_p=sum(math.comb(n,k) for k in range(rescue,n+1))/2**n if n else 1.0
    groups=rows(OUT/'R2B_GROUPS.tsv'); contexts=rows(OUT/'R2B_CONTEXTS.tsv')
    for g in groups:
        sub=[float(r['Delta_VS']) for r in primary if r['context']==g['context'] and r['truth_source']==g['truth_source']]
        assert len(sub)==4 and abs(statistics.mean(sub)-float(g['mean_Delta_VS']))<1e-14
    cv=[float(r['mean_Delta_VS']) for r in contexts]; observed=statistics.mean(cv)
    p=sum(statistics.mean(x*s for x,s in zip(cv,signs))>=observed-1e-15
          for signs in itertools.product((-1,1),repeat=8))/256
    result=json.loads((OUT/'R2B_RESULT.json').read_text())
    assert (vs,es,rescue,harm)==(result['VS_correct'],result['ES_correct'],result['rescues'],result['harms'])
    assert p==result['summary']['exact_signflip'] and paired_p==result['discordant_exact_binomial_p']
    audit=dict(integer_formula_checks=512,target_omission_delta_checks=256,max_absolute_delta_error=max_error,
               sign_mismatches=mismatched_signs,strict_tie_rule_verified=not mismatched_signs,
               independent_group_mean_checks=16,independent_signflip=p,
               independent_paired_binomial_p=paired_p,VS_correct=vs,ES_correct=es,rescues=rescue,harms=harm)
    (OUT/'R2B_INDEPENDENT_ARITHMETIC.json').write_bytes((json.dumps(audit,indent=2,sort_keys=True)+'\n').encode())
    print(json.dumps(audit,indent=2,sort_keys=True))
    assert not mismatched_signs


if __name__=='__main__':
    main()
