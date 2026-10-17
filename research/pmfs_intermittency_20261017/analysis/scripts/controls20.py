"""Frozen ordinary controls on captured, immutable forward maps. No ROS."""
from pathlib import Path
import csv,json,subprocess,time
import numpy as np,yaml
from scipy.special import betaincinv
from parameters import read_parameters
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA';O=R/'results';T=O/'controls';T.mkdir(exist_ok=True)
entries=json.loads((P/'CASE_INDEX.json').read_text())['cases'];qa=json.loads((O/'REPLAY20_QA.json').read_text());bad={r['case'] for r in qa if r['status']!='PASS'}
def read(p):return list(csv.DictReader(p.open()))
def sigmoid(x):return np.exp(-np.logaddexp(0,-x))
rows=[];parity=[];decoder=[];groups=[];allinput=[]
for e in entries:
 c=e['case'];root=P/e['native_path'];ev=np.loadtxt(root/'runtime/measurement_events.csv',delimiter=',',ndmin=2);par,parameter_origin=read_parameters(root);D=par['sourceDiscriminationPower'];prior=par.get('hitPriorProbability',.3);truth=np.asarray(e['metadata']['source_xyz'][:2]);previous=None;cppresults=None
 updates=sorted((root/'runtime/updates').glob('*/COMPLETE.txt'),key=lambda x:int(x.parent.name.split('_')[-1]))
 for marker in updates:
  prefix=marker.parent;u=prefix.name;m=json.loads((prefix/'metadata.json').read_text());inp=read(prefix/'input.csv');N=len(inp);free=np.array([i for i,r in enumerate(inp) if r['occupancy']=='1']);nf=len(free);n=int(np.searchsorted(ev[:,0],m['stamp_ns'],side='right'));q0=np.fromfile(prefix/'posterior.f64',dtype='<f8');ps=sigmoid(np.array([float(inp[i]['logOdds']) for i in free]));conf=np.array([float(inp[i]['confidence']) for i in free]);calls=read(prefix/'candidates.csv');cd={x['candidate_id']:x for x in calls};leaves=[a for a in read(prefix/'final_tree.csv') if a['has_children']=='0' and a['node_id'] in cd];ids=[a['node_id'] for a in leaves]
  xy=np.c_[np.float32(m['origin_x'])+(free%m['width']+np.float32(.5))*np.float32(m['cell_size']),np.float32(m['origin_y'])+(free//m['width']+np.float32(.5))*np.float32(m['cell_size'])];ti=int(np.float32(np.float32(truth[0])-np.float32(m['origin_x']))/np.float32(m['cell_size']))+int(np.float32(np.float32(truth[1])-np.float32(m['origin_y']))/np.float32(m['cell_size']))*m['width'];tloc=np.flatnonzero(free==ti);tloc=int(tloc[0]) if len(tloc) else None
  owner=np.full(nf,-1,int)
  for j,a in enumerate(leaves):
   mask=(free%m['width']>=int(a['origin_i']))&(free%m['width']<int(a['origin_i'])+int(a['size_i']))&(free//m['width']>=int(a['origin_j']))&(free//m['width']<int(a['origin_j'])+int(a['size_j']));assert (owner[mask]==-1).all();owner[mask]=j
  assert (owner>=0).all(),(c,u,'unowned cells')
  h=np.array([np.fromfile(prefix/cd[a]['map_file'],dtype='<f4')[free] for a in ids]);hn=[]
  for a in ids:
   raw=prefix/cd[a]['map_file'].replace('.f32','_unblurred.f32');hn.append(np.fromfile(raw,dtype='<f4')[free])
  rawh=np.array(hn)
  ll0=np.log(1-D*conf[None,:]*np.abs(ps[None,:]-h)).sum(axis=1);f=ll0[owner];q=np.exp(f-f.max());q/=q.sum();qe=float(abs(q-q0[free]).max());le=float(max(abs(ll0[j]-float(cd[a]['logscore'])) for j,a in enumerate(ids)));parity.append(dict(case=c,update=u,candidate_logscore_max_error=le,posterior_max_error=qe,free_cells=nf,final_owners=len(ids)));assert qe<2e-8 and le<.002,(c,u,qe,le)
  comp=None if previous is None else int(previous);cloc=np.flatnonzero(free==comp) if comp is not None else np.array([],int);cloc=int(cloc[0]) if len(cloc) else None;towner=owner[tloc] if tloc is not None else None;cowner=owner[cloc] if cloc is not None else None
  previous=int(free[np.argmax(q0[free])])
  nativeonly=c in bad
  if nativeonly:maps={'O0':ps};confmaps={'native':conf}
  else:
   replay=np.fromfile(O/'replay20'/(c+'.f64'),dtype='<f8').reshape(len(ev),nf,4)[:n];w=replay[:,:,2];coverage=replay[:,:,3];assert np.isfinite(w).all() and (w>=0).all() and (w<=1+1e-12).all();y=(ev[:n,1]>par['th_gas_present']).astype(float);weight=w.sum(axis=0);hits=y@w;emp=np.divide(hits,weight,out=np.full(nf,prior),where=weight>0);beta=(prior+hits)/(1+weight);blockw=np.zeros(nf);blockhit=np.zeros(nf);blockcoverage=np.zeros(nf)
   for stop in np.unique(ev[:n,6]):
    keep=ev[:n,6]==stop;blockw+=w[keep].mean(axis=0);blockhit+=(y[keep]@w[keep])/keep.sum();blockcoverage+=coverage[keep].mean(axis=0)
   block=(prior+blockhit)/(1+blockw);blockconf=1-np.exp(-blockcoverage/(par['confidenceMeasurementWeight']**2))
   if cppresults is None:
    meta=T/(c+'_ordinary_meta.txt');meta.write_text(f'{len(ev)} {nf} {prior}\n'+'\n'.join(f'{int(v[6])} {int(v[1]>par["th_gas_present"])}' for v in ev)+'\n');co=T/(c+'_ordinary.f64');q=subprocess.run([str(R/'build/ordinary_controls'),str(meta),str(O/'replay20'/(c+'.f64')),str(co),str(par['confidenceMeasurementWeight'])],capture_output=True,text=True);assert q.returncode==0,(c,q.stderr);cppresults=np.fromfile(co,dtype='<f8').reshape(len(ev),nf,4)
   cc=cppresults[n-1];cpp_error=max(float(abs(v-cc[:,j]).max()) for j,v in enumerate([emp,beta,block,blockconf]));assert cpp_error<2e-12,(c,u,cpp_error)
   parity[-1]['ordinary_cpp_numpy_max_error']=cpp_error
   maps={'O0':ps,'O1':cc[:,0],'O2':cc[:,1],'O3':cc[:,2]};confmaps={'native':conf,'blocks':cc[:,3]}
  archive={'free_indices':free,'owner':owner,'native_q':q0[free],'candidate_ids':np.asarray(ids),'forward_blurred':h,'forward_unblurred':rawh}
  if not nativeonly:
   archive['O2_interval_lower']=betaincinv(prior+hits,1-prior+weight-hits,.025)
   archive['O2_interval_upper']=betaincinv(prior+hits,1-prior+weight-hits,.975)
   archive['O3_interval_lower']=betaincinv(prior+blockhit,1-prior+blockw-blockhit,.025)
   archive['O3_interval_upper']=betaincinv(prior+blockhit,1-prior+blockw-blockhit,.975)
  for label,p in maps.items():archive[label]=p
  poses=ev[:n,4:6];near=np.min(np.linalg.norm(xy[:,None,:]-poses[None,:,:],axis=2),axis=1)<=.5
  for fmode,hh in [('native_blur',h),('raw_center',rawh)]:
   for cmod,confidence in confmaps.items():
    for arm,p in maps.items():
     ll=np.log(1-D*confidence[None,:]*np.abs(p[None,:]-hh)).sum(axis=1);cellll=ll[owner];qq=np.exp(cellll-cellll.max());qq/=qq.sum()
     # Keep original doubles for O0 readout: tiny recomputation differences can
     # change std::sort ordering when cell probabilities are exactly tied.
     if arm=='O0' and cmod=='native' and fmode=='native_blur':qq=q0[free].copy()
     key='__'.join([arm,cmod,fmode]);archive[key]=qq
     rank=1+int(np.sum(qq>qq[tloc])) if tloc is not None else None;ties=int(np.sum(qq==qq[tloc])) if tloc is not None else None;order=np.argsort(-qq,kind='stable');massabove=float(qq[qq>qq[tloc]].sum()) if tloc is not None else None;mean=qq@xy;masktruth=np.linalg.norm(xy-truth,axis=1)<=1.5
     r=dict(case=c,update=u,arm=arm,confidence=cmod,forward=fmode,windows=n,source_supported=tloc is not None,qualified_history=not nativeonly,competitor_locked_cell=comp,competitor_rule='ABSTAIN_FIRST_EPOCH' if comp is None else 'PREVIOUS_NATIVE_ROW_MAJOR_MAX',same_owner=towner==cowner if towner is not None and cowner is not None else None,truth_rank=rank,truth_rank_ties=ties,truth_mass=float(qq[tloc]) if tloc is not None else 0,truth_mass_1p5m=float(qq[masktruth].sum()),mass_strictly_above_truth=massabove,truth_in90=(massabove<.9) if massabove is not None else False,working_nll=-float(np.log(qq[tloc])) if tloc is not None else None,working_brier=float(np.sum(qq**2)+1-2*qq[tloc]) if tloc is not None else None,map_error_m=float(np.linalg.norm(xy[np.argmax(qq)]-truth)),source_score_gap=float(ll[towner]-ll[cowner]) if towner is not None and cowner is not None else None,original_native_outcome='SEE_NATIVE20_CASE_COMPARISON',task_gain_claim=False)
     if towner is not None and cowner is not None:
      delta=np.log(1-D*confidence*np.abs(p-hh[towner]))-np.log(1-D*confidence*np.abs(p-hh[cowner]));r.update(gap_near_sample=float(delta[near].sum()),gap_far_from_sample=float(delta[~near].sum()));archive[key+'__contrast']=delta
     groups.append((m,free,qq));decoder.append(r);rows.append(r)
  np.savez_compressed(T/(c+'_'+u+'.npz'),**archive)
  (O/'STRONG_CONTROLS.json').write_text(json.dumps(rows,indent=2,default=lambda x:x.item()));(O/'SOURCE_SCORE_PARITY.json').write_text(json.dumps(parity,indent=2));print(c,u,n,nf,len(ids),qe,flush=True)
lines=[str(len(groups))]
for m,free,q in groups:
 lines.append(' '.join(map(str,[m['width'],m['height'],m['origin_x'],m['origin_y'],m['cell_size'],len(free)])));lines.extend(f'{i} {v:.17g}' for i,v in zip(free,q))
(T/'readout_input.txt').write_text('\n'.join(lines)+'\n');t=time.time();p=subprocess.run([str(R/'build/readout2026'),str(T/'readout_input.txt')],capture_output=True,text=True);(R/'logs/readout.json').write_text(json.dumps(dict(command=p.args,returncode=p.returncode,stderr=p.stderr,elapsed_s=time.time()-t),indent=2));assert p.returncode==0,p.stderr
(T/'readout.csv').write_text(p.stdout);out=list(csv.DictReader(p.stdout.splitlines()));assert len(out)==len(rows)
index={e['case']:e for e in entries}
for r,d in zip(rows,out):
 truth=np.array(index[r['case']]['metadata']['source_xyz'][:2]);r['official_top5_error_m']=float(np.linalg.norm(np.array([float(d['top5_x']),float(d['top5_y'])])-truth));r['posterior_mean_error_m']=float(np.linalg.norm(np.array([float(d['mean_x']),float(d['mean_y'])])-truth));r['variance_m2']=float(d['variance_m2'])
keys=list(dict.fromkeys(k for r in rows for k in r))
with (O/'STRONG_CONTROLS.csv').open('w',newline='') as f:w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
(O/'STRONG_CONTROLS.json').write_text(json.dumps(rows,indent=2,default=lambda x:x.item()));print('COMPLETE',len(rows),'fixed-history readouts; no counterfactual ROS outcomes.')
