"""Frozen source-blind native 3D sparse observation preflight."""
from pathlib import Path
import csv, json, hashlib, datetime
import numpy as np
HERE = Path(__file__).resolve().parent
OLD = Path('C:/Users/50176/Documents/Codex/2026-10-05/codex-pmfs-pmfs-task-sufficient-world/outputs')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(name, obj): (HERE/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
def csvout(name, rows):
    with (HERE/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
if (HERE/'ROUTE_PREFLIGHT_DECISION.json').exists(): raise RuntimeError('Preserve completed preflight')
protocol=json.loads((HERE/'ROUTE_PROTOCOL_FROZEN.json').read_text())
dump('ROUTE_PRE_SCORE_SEAL.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protocol_sha256':sha(HERE/'ROUTE_PROTOCOL_FROZEN.json'),'code_sha256':sha(__file__),'new_simulations':0})
decision=json.loads((HERE/'STAGE0_DECISION.json').read_text())
configs=json.loads((OLD/'R0C/FROZEN_CONFIGS_32.json').read_text())
runs=json.loads((OLD/'P0/RUNS_64_FROZEN.json').read_text())
rows=[]; lineage=[]; route_rows=[]; post_rows=[]; eligible=True; arrays={}
for case in decision['selected_cases']:
    rs=sorted([r for r in runs if r['house']==case['house'] and r['wind_label']==case['wind'] and r['gas_type']==13 and r['source']==case['source']],key=lambda r:r['realization'])
    house=case['house']; route=None; ids=None
    for r in rs:
        stem=OLD/'R0C/fields'/r['run_id']
        coords=np.genfromtxt(str(stem)+'.coords.csv',delimiter=',',skip_header=1)
        frames=np.genfromtxt(str(stem)+'.frames.csv',delimiter=',',skip_header=1)
        field=np.memmap(str(stem)+'.fields.f32',dtype='<f4',mode='r',shape=(len(frames),len(coords)))
        with np.load(OLD/'P0/states'/(r['run_id']+'.npz')) as z:
            lo=z['lo']; span=z['span']; fp=z['footprint']; m=(z['times']>=100)&(z['times']<=700); fp=fp[m].astype(float); total=fp.sum((1,2))
            row={'run_id':r['run_id']}
            for side,edge in [('xmin',fp[:,:,:3]),('xmax',fp[:,:,-3:]),('ymin',fp[:,:3,:]),('ymax',fp[:,-3:,:])]: row[side+'_mean_mass_fraction']=float((edge.sum((1,2))/total).mean())
            rows.append(row)
        if route is None:
            altitude=float(coords[np.argmin(abs(coords[:,2]-0.3)),2]); plane=np.flatnonzero(np.isclose(coords[:,2],altitude,atol=1e-6))
            points=[]
            for j,y in enumerate(np.linspace(.1,.9,6)):
                xs=np.linspace(.1,.9,6)
                if j%2: xs=xs[::-1]
                for x in xs: points.append(lo[:2]+np.array([x,y])*span[:2])
            targets=np.array(points[:31]); ids=np.array([plane[np.argmin(np.sum((coords[plane,:2]-p)**2,axis=1))] for p in targets]); route=coords[ids].copy()
            for j,xyz in enumerate(route): route_rows.append({'house':house,'time_s':100+20*j,'x':float(xyz[0]),'y':float(xyz[1]),'z':float(xyz[2]),'free_voxel_id':int(ids[j])})
        assert np.allclose(coords[ids],route,rtol=0,atol=1e-8)
        idx=np.array([np.flatnonzero(frames[:,0]==t)[0] for t in range(100,701,20)])
        c=np.array(field[idx,ids],dtype=float); assert np.isfinite(c).all() and (c>=0).all()
        arrays[(house,r['source'],r['realization'])]=c
        for ext in ['coords.csv','frames.csv','fields.f32','parity.csv']:
            p=Path(str(stem)+'.'+ext); lineage.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
        for j,value in enumerate(c): post_rows.append({'run_id':r['run_id'],'source':r['source'],'realization':r['realization'],'time_s':100+20*j,'native_ppm':float(value)})
    # Both candidates must be preflighted independently, after all data loading.
csvout('STAGE0_ALL_SIDES_SECONDARY_DIAGNOSTIC.csv',rows)
csvout('ROUTE_GEOMETRY_POINTS.csv',route_rows)
csvout('ROUTE_BASELINE_NATIVE_CONCENTRATIONS.csv',post_rows)
csvout('ROUTE_INPUT_LINEAGE_SHA256.csv',lineage)
predictions=[]
for (house,s,r),obs in sorted(arrays.items()):
    candidates=sorted({ss for h,ss,rr in arrays if h==house}); assert len(candidates)==2
    for baseline in ['forward_hit_probability','source_term_log_gaussian']:
        scores=[]
        for candidate in candidates:
            train=np.stack([arrays[(house,candidate,rr)] for rr in range(1,5) if rr!=r])
            if baseline=='forward_hit_probability':
                p=((train>=protocol['hit_threshold_ppm']).sum(axis=0)+.5)/(len(train)+1)
                hits=obs>=protocol['hit_threshold_ppm']; ll=float(np.sum(np.where(hits,np.log(p),np.log1p(-p))))
            else:
                train=np.log1p(train); var=np.maximum(train.var(axis=0,ddof=1),.25**2); mu=train.mean(axis=0)
                ll=float(-.5*np.sum(np.log(2*np.pi*var)+(np.log1p(obs)-mu)**2/var))
            scores.append(ll)
        p=np.exp(np.array(scores)-max(scores)); p=p/p.sum(); true_i=candidates.index(s)
        ambiguous=bool(abs(p[0]-p[1])<=1e-12)
        predictions.append({'house':house,'source':s,'realization':r,'baseline':baseline,'detectable_points':int((obs>=protocol['hit_threshold_ppm']).sum()),'max_native_ppm':float(obs.max()),'posterior_true_source':float(p[true_i]),'posterior_nll':float(-np.log(max(p[true_i],1e-300))),'correct':bool(np.argmax(p)==true_i and not ambiguous),'ambiguous':ambiguous})
summaries=[]
for house,s in sorted({(h,ss) for h,ss,r in arrays}):
    for baseline in ['forward_hit_probability','source_term_log_gaussian']:
        ps=[p for p in predictions if p['house']==house and p['source']==s and p['baseline']==baseline]
        correct=sum(p['correct'] for p in ps); detects=sum(p['detectable_points']>0 for p in ps); ok=correct>=3 and detects>=3
        summaries.append({'house':house,'source':s,'baseline':baseline,'correct_of_4':correct,'detectable_runs_of_4':detects,'pass':ok})
        eligible=eligible and ok
csvout('ROUTE_ORACLE_BASELINE_PREDICTIONS.csv',predictions)
dump('ROUTE_PREFLIGHT_DECISION.json',{'status':'W0C_OBSERVATION_PREFLIGHT_PASS' if eligible else 'W0C_OBSERVATION_PREFLIGHT_HOLD','summaries':summaries,'new_simulations':0,'route_protocol_sha256':sha(HERE/'ROUTE_PROTOCOL_FROZEN.json'),'interpretation':'This preflight tests whether the frozen idealized sparse observation has source evidence under oracle wind. A failed preflight cannot test matched-error transport anisotropy and is not a causal STOP.'})
print(json.dumps({'eligible':eligible,'summaries':summaries,'predictions':predictions},indent=2))
