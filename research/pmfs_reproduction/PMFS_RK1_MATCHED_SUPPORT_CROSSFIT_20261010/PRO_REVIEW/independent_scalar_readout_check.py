"""Independent CSV/integer-count recomputation of the inspected PRO readout controls.
No imports from PRO scripts, no pandas grouping, no transport integrations.
"""
import sys
sys.dont_write_bytecode=True
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np,cv2
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(p,a):
    with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
def run(root,out):
    m1=root/'M3_NEW/M1_REFERENCE';m2=root/'M2_FROZEN';m3=root/'M3_NEW'
    inputrows=rows(m1/'snapshot/input.csv');meta=json.loads((m2/'native_reference_evidence/FROZEN_METADATA.json').read_text())
    shape=(meta['height'],meta['width']);n=len(inputrows);free=np.array([int(r['occupancy'])==1 for r in inputrows]);assert free.sum()==447
    p=np.array([1-1/(1+math.exp(float(r['logOdds']))) for r in inputrows]);c=np.array([float(r['confidence']) for r in inputrows])
    mask=free.astype(np.float32).reshape(shape)
    gb=lambda v:cv2.GaussianBlur(np.asarray(v,dtype=np.float32).reshape(shape),(0,0),1.5,1.5)
    def score(a):return math.fsum(math.log1p(-.4*float(c[i])*abs(float(p[i])-float(a[i]))) for i in np.flatnonzero(free))
    cf=rows(m3/'projected_center_field/CENTER_FIELD_PER_CELL.csv');a2={};fields={};counts=[]
    for s in ['C7','K2']:
        for variant in ['MASKED','ALL_XY']:
            rr=[r for r in cf if r['candidate_id']==s and r['variant']==variant and r['stage']=='UNBLURRED']
            assert len(rr)==n
            arr=np.zeros(n,dtype=np.float32);covered=set()
            for r in rr:
                i=int(r['cell_index']);assert i not in covered;covered.add(i);arr[i]=np.float32(float(r['frequency']))
            assert len(covered)==n;fields[s,variant]=arr
        hitcounts=np.zeros(n,dtype=np.int64);events=np.zeros(n,dtype=np.int64)
        for rep in [0,1]:
            seen=set();threshold_equal=0;native_float_threshold_disagreements=0
            for r in rows(m2/f'native_reference_evidence/realizations/{s}_{rep}/QUERY_OUTPUT.csv'):
                # Accept primary membership branch v0 only; reject duplicate
                # identities independently of the provider's grouped mean.
                parts=r['query_id'].split('_')
                if len(parts)!=4 or parts[0]!='grid' or parts[2]!='v0':continue
                block=int(parts[1][1:]);cell=int(parts[3][1:]);identity=(block,cell)
                assert identity not in seen and free[cell];seen.add(identity)
                ppm=float(r['ppm_float32']);events[cell]+=1;hitcounts[cell]+=int(ppm>.1)
                threshold_equal+=ppm==float(np.float32(.1))
                native_float_threshold_disagreements+=int(ppm>.1)!=int(np.float32(ppm)>np.float32(.1))
            assert len(seen)==50*447
            counts.append(dict(bank=f'{s}_{rep}',primary_grid_events=len(seen),distinct_cells=447,exact_float32_threshold_values=threshold_equal,threshold_double_vs_float32_disagreements=native_float_threshold_disagreements))
        assert np.all(events[free]==100) and not np.any(events[~free])
        pid=np.zeros(n);pid[free]=hitcounts[free]/events[free]
        for name,arr in [('PID_THRESHOLD',pid),('PROJECTED_CENTER',fields[s,'MASKED'])]:
            den=gb(mask);num=gb(arr);bl=np.clip(np.divide(num,den,out=num.copy(),where=den!=0),0,1).ravel()
            for stage,aa in [('UNBLURRED',arr),('SAME_NAV_BLUR',bl)]:a2[s,name,stage]=score(aa)
    res=[]
    for name in ['PID_THRESHOLD','PROJECTED_CENTER']:
        for stage in ['UNBLURRED','SAME_NAV_BLUR']:
            t=a2['C7',name,stage];w=a2['K2',name,stage];d=t-w
            res.append(dict(readout=name,stage=stage,C7_log_score=t,K2_log_score=w,true_minus_wrong_log=d,selected='C7' if d>0 else 'K2'))
    factorial=[]
    for numerator in ['NAV_MASKED','ALL_XY']:
        for denominator in ['NAV_MASK','ALL_FRAME']:
            vals={}
            for s in ['C7','K2']:
                q=fields[s,'ALL_XY'];num=gb(q*free if numerator=='NAV_MASKED' else q)
                den=gb(mask if denominator=='NAV_MASK' else np.ones(shape,np.float32))
                pre=np.divide(num,den,out=num.copy(),where=den!=0).ravel();cl=np.clip(pre,0,1)
                vals[s]=score(cl)
                factorial.append(dict(candidate=s,numerator=numerator,denominator=denominator,log_score=vals[s],nav_cells_clipped_above_one=int(((pre>1)&free).sum()),max_nav_preclip=float(pre[free].max())))
    references=rows(out.parent/'handoff/new_diagnostics/SAME_BANK_SAME_SCORER_MARGINS.csv')
    errors=[]
    for r,ref in zip(res,references):
        assert r['readout']==ref['readout'] and r['stage']==ref['stage'] and r['selected']==ref['selected']
        err=abs(r['true_minus_wrong_log']-float(ref['true_minus_wrong_log']));assert err<3e-12;errors.append(err)
    fa=rows(out.parent/'handoff/new_diagnostics/READOUT_MASK_DENOMINATOR_FACTORIAL.csv');lookup={(r['source'],r['numerator'],r['denominator']):r for r in fa}
    for r in factorial:
        ref=lookup[r['candidate'],r['numerator'],r['denominator']]
        assert r['nav_cells_clipped_above_one']==int(ref['nav_cells_clipped_above_one'])
        for k in ['log_score','max_nav_preclip']:assert math.isclose(r[k],float(ref[k]),rel_tol=2e-12,abs_tol=3e-13)
    out.mkdir(parents=True,exist_ok=True);write(out/'INDEPENDENT_SAME_SCORER_MARGINS.csv',res);write(out/'INDEPENDENT_MASK_DENOMINATOR_FACTORIAL.csv',factorial);write(out/'INDEPENDENT_GRID_EVENT_IDENTITY_COUNTS.csv',counts)
    result=dict(verdict='PASS_INDEPENDENT_INTEGER_EVENT_COUNTS_AND_SCALAR_LOG_RECOMPUTATION',new_forwards=0,new_gas=0,new_ROS=0,
        maximum_pair_margin_absolute_difference=max(errors),margins=res,factorial=factorial,event_integrity=counts,
        cv2_version=cv2.__version__,numpy_version=np.__version__,limits=['Same saved reference banks and fixed scorer only; no heldout re-selection or new source posterior.','Full-field grid probes are oracle diagnostic inputs, not extra deployable sensor data.','Post-inspection mask ablations are exploratory; their scores are not calibrated physical likelihoods.'])
    (out/'INDEPENDENT_SCALAR_CHECK_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--combined-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.combined_root,a.out),indent=2))
