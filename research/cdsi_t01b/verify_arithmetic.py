"""Independent direct-sum check of all FULL/STATIC Energy permutations."""
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/cdsi_t01b'
OUT=EV/'pass1'


def rows(path):
    with path.open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f,delimiter='\t'))


def main():
    manifest=rows(OUT/'EXACT_64_RUN_MANIFEST.tsv')
    nulls=rows(OUT/'EXACT_70_ASSIGNMENT_NULLS.tsv')
    results=rows(OUT/'CONTEXT_ENERGY_RESULTS.tsv')
    combinations=list(itertools.combinations(range(8),4))
    checks=[]
    observed=[]
    for c in range(8):
        context=f'X{c:02d}'
        runs=sorted([r for r in manifest if r['context']==context],key=lambda r:(r['source_id'],int(r['replicate_ordinal'])))
        x=np.stack([np.load(ROOT/'evidence/ocb_r2/mechanism_census_r0/inputs'/(r['run_id']+'.pooled.npy'),allow_pickle=False)>0 for r in runs])
        for arm,values in [('FULL_DYNAMIC_300D',x.reshape(8,300).astype(float)),('STATIC_COLLAPSED_30D',x.mean(axis=1))]:
            normalized=np.empty((8,8))
            for i in range(8):
                for j in range(8):
                    normalized[i,j]=math.sqrt(sum(float(z)**2 for z in values[i]-values[j])/values.shape[1])
            direct=[]
            for a in combinations:
                b=[i for i in range(8) if i not in a]
                ab=sum(normalized[i,j] for i in a for j in b)/16
                aa=sum(normalized[i,j] for i in a for j in a)/16
                bb=sum(normalized[i,j] for i in b for j in b)/16
                direct.append(2*ab-aa-bb)
            saved=sorted([r for r in nulls if r['context']==context and r['arm']==arm],key=lambda r:int(r['assignment_index']))
            error=max(abs(float(r['energy'])-d) for r,d in zip(saved,direct))
            assert len(saved)==70 and error<1e-12
            reported=next(r for r in results if r['context']==context and r['arm']==arm)
            p=sum(v>=direct[0]-1e-12 for v in direct)/70
            z=(direct[0]-np.mean(direct))/np.std(direct)
            assert abs(p-float(reported['exact_p']))<1e-12 and abs(z-float(reported['z']))<1e-10
            checks.append(dict(context=context,arm=arm,assignments=70,max_abs_error=error,exact_p_matches=True,z_matches=True))
            if arm=='FULL_DYNAMIC_300D':
                observed.append(float(reported['z']))
    draws=np.load(OUT/'C2_ALL_ASSIGNMENT_DRAW_ENERGIES.npy',allow_pickle=False)
    assert draws.shape==(8,70,1000)
    comp=[combinations.index(tuple(i for i in range(8) if i not in a)) for a in combinations]
    for c in range(8):
        mean=draws[c].mean(axis=1)
        sym=(mean+mean[comp])/2
        saved=sorted([r for r in nulls if r['context']==f'X{c:02d}' and r['arm']=='C2_PAIRING_DESTROYED'],key=lambda r:int(r['assignment_index']))
        assert np.allclose(sym,[float(r['energy']) for r in saved],atol=1e-12,rtol=0)
    aggregate=json.loads((OUT/'AGGREGATE_PERMUTATION.json').read_text(encoding='utf-8'))
    anull=np.load(OUT/'STRATIFIED_AGGREGATE_PERMUTATION.npy',allow_pickle=False)
    assert abs(np.mean(observed)-aggregate['observed'])<1e-12
    assert np.count_nonzero(anull>=aggregate['observed']-1e-12)==aggregate['exceedances']
    result=dict(pass_=True,direct_full_static_assignment_checks=8*2*70,checks=checks,
        c2_draw_to_report_arithmetic_pass=True,aggregate_exceedance_pass=True,
        secondary_scientific_scorer_added=False,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (EV/'INDEPENDENT_ARITHMETIC_CHECK.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(pass_=True,direct_checks=1120),sort_keys=True))


if __name__=='__main__':
    main()
