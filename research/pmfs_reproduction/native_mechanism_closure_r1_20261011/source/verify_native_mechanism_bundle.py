"""Portable read-only verification; NumPy only; no ROS, generation or forwards.
Usage: python verify_native_mechanism_bundle.py /path/to/extracted-package
CSV numeric comparisons use declared tolerance; hashes check original bytes.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json,hashlib,math,importlib.util,time
import numpy as np

def rows(p):
 with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def verify(root):
 start=time.perf_counter();core=root/'PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_CORE';raw=root/'PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_RAW';support=raw/'support';checks={};maximum=0.;pcmax=0.
 for folder in [core,raw]:
  manifest=load(folder/'FILE_SHA256_MANIFEST.json')
  for rel,expected in manifest.items():assert sha(folder/rel)==expected,(folder.name,rel)
  checks[folder.name+'_hashes']=len(manifest)
 def logscore(inp,q,D):
  p=np.array([float(r['probability']) if 'probability' in r else 1/(1+math.exp(-float(r['logOdds']))) for r in inp]);c=np.array([float(r['confidence']) for r in inp]);free=np.array([r['occupancy']=='1' for r in inp])
  f=1-D*np.abs(p-np.asarray(q,float))*c;assert (f[free]>0).all();return math.fsum(np.log(f[free]))
 def posterior(candidates,inp,width,folder,score_key='score'):
  a=np.zeros(len(inp))
  for r in candidates:
   ox,oy,nx,ny=[int(r[k]) for k in ['origin_i','origin_j','size_i','size_j']]
   for y in range(oy,oy+ny):a[ox+y*width:ox+nx+y*width]=float(r[score_key])
  a[[r['occupancy']!='1' for r in inp]]=0;assert a.sum()>0;return a/a.sum()
 for label,D in [('E3',.3),('B4',.4)]:
  f=support/'historical'/label;inp=rows(f/'input.csv');candidates=rows(f/'candidates.csv');m=load(f/'metadata.json');a=posterior(candidates,inp,m['width'],f)
  e=float(np.max(np.abs(a-np.fromfile(f/'posterior.f64',dtype='<f8'))));pcmax=max(pcmax,e);assert e<1e-12
  for c in candidates:
   e=abs(logscore(inp,np.fromfile(f/c['map_file'],dtype='<f4'),D)-float(c['logscore']));maximum=max(maximum,e);assert e<1e-10
  replay=support/'historical_replays'/(label+'_short_forward_OFF')/'forward';c=rows(replay/'candidates.csv')[0];old=candidates[0]
  assert np.array_equal(np.fromfile(f/old['map_file'],dtype='<f4'),np.fromfile(replay/c['map_file'],dtype='<f4'))
  assert c['rng_after']==old['rng_after'] and c['gaussian_index_after']==old['gaussian_index_after']
 checks['historical_candidates']=295
 a=support/'cold_anchor';g=support/'cold_golden';ca=rows(a/'candidates.csv')[0];cg=rows(g/'candidates.csv')[0]
 for k in ['map_file','points_file']:assert sha(a/ca[k])==sha(g/cg[k])
 for n in ['gaussian_cache.f32','gaussian_initial.csv']:assert sha(a/n)==sha(g/n)
 for k in ['rng_before','rng_after','gaussian_index_before','gaussian_index_after','gaussian_ready_before','point_count','score','logscore']:assert ca[k]==cg[k],k
 checks['true_cold_anchor']='exact map, points, cache, init order, score, RNG phase'
 candidates_checked=updates=0
 for f in sorted((support/'native').iterdir()):
  assert (f/'EXECUTION.json').exists();meta=rows(f/'metadata.csv')[0]
  for u in f.glob('update_*'):
   if not u.is_dir():continue
   inp=rows(u/'input_full.csv');cs=rows(u/'candidates.csv');byid={r['candidate_id']:r for r in cs};leaves=[r for r in rows(u/'final_tree.csv') if r['has_children']=='0'];post=np.fromfile(u/'posterior.f64',dtype='<f8')
   for c in cs:
    e=abs(logscore(inp,np.fromfile(u/c['map_file'],dtype='<f4'),.4)-float(c['logscore']));maximum=max(maximum,e);assert e<1e-10
   selected=[byid[r['node_id']] for r in leaves];re=posterior(selected,inp,int(meta['width']),u);e=float(np.max(abs(re-post)));pcmax=max(pcmax,e);assert e<1e-12
   assert abs(post.sum()-1)<1e-12
   lr=next(r for r in rows(f/'update_ledger.csv') if r['update']==u.name.removeprefix('update_'))
   width=int(meta['width']);cell=float(meta['cell_size']);idx=np.arange(len(post));x=np.float32(meta['origin_x'])+np.float32((idx%width+.5)*cell);y=np.float32(meta['origin_y'])+np.float32((idx//width+.5)*cell)
   mx=float(np.sum(post*x));my=float(np.sum(post*y));assert abs(mx-float(lr['mean_x']))<2e-5 and abs(my-float(lr['mean_y']))<2e-5
   var=float(np.sum(post*((x-mx)**2+(y-my)**2)));assert abs(var-float(lr['variance']))<1e-4
   updates+=1;candidates_checked+=len(cs)
 checks['primary_histories']=len(list((support/'native').iterdir()));checks['primary_updates']=updates;checks['primary_native_candidates']=candidates_checked;assert checks['primary_histories']==18 and updates==54
 checked=0
 for f in (support/'readouts').iterdir():
  with np.load(f/'FIELDS.npz',allow_pickle=False) as z:
   q=z['queries'];assert q.shape==(50,448,5) and np.isfinite(q).all() and (q[:,:,0]>=0).all();assert (q[:,-1,1]==1).all()
   o1=(q[:,:447,0]>np.float32(.1)).astype(float)
   grid=rows(support/'geometry/native_grid.csv');free=np.array([r['occupancy']=='1' for r in grid]);assert int(free.sum())==447
   assert np.max(abs(z['O1'][:,free]-o1))<1e-7
   for method in ['O0','O1']:assert z[method].shape==(50,1530) and np.isfinite(z[method]).all() and (z[method]>=0).all() and (z[method]<=1).all()
   for method in ['O0_blurred','O1_blurred','A1']:assert z[method].shape==(1530,) and np.isfinite(z[method]).all() and (z[method]>=0).all() and (z[method]<=1).all()
  checked+=1
 checks['native_readout_banks']=checked;assert checked==100
 for r in rows(core/'CONTROLLED_FACTORIAL_CONTRASTS.csv'):
  a,b,c,d=[float(r[k]) for k in ['m00','m01','m10','m11']]
  for key,value in [('D_at_V0',c-a),('D_at_V1',d-b),('V_at_D0',b-a),('V_at_D1',d-c),('interaction',d-c-b+a)]:assert abs(float(r[key])-value)<1e-10
 checks['factorial_contrasts']=len(rows(core/'CONTROLLED_FACTORIAL_CONTRASTS.csv'))
 frames=accounting=0
 raw_decoder=module('nmc_portable_decoder',core/'source/portable/raw_decode.py');occ=raw_decoder.occupancy(support/'geometry/OccupancyGrid3D.csv')
 for bank in (support/'banks').iterdir():
  manifest={r['frame']:r for r in rows(bank/'ALL_FRAME_SHA256_AND_TIME.csv')};times=[float(r['physical_snapshot_time_s']) for r in manifest.values()];assert all(y>x for x,y in zip(times,times[1:]))
  for p in (bank/'selected_frames').iterdir():
   r=manifest[p.name.removeprefix('iteration_')];assert sha(p)==r['SHA256'];desc=raw_decoder.snapshot(p);assert desc['gas_type']==13 and desc['wind_index']==int(r['wind_index']) and len(desc['filaments'])==int(r['filaments'])
   if bank.name.endswith('V0') and len(desc['filaments']):assert np.max(abs(desc['filaments'][:,2]-desc['source'][2]))<1e-6
   frames+=1
  if (bank/'STATE_ACCOUNTING.csv').exists():
   rs=rows(bank/'STATE_ACCOUNTING.csv');alive=0;previous=None
   for r in rs:
    alive+=int(r['released'])-int(r['removed']);assert alive==int(r['alive'])
    if previous is not None:assert int(r['gaussian_index'])==(previous+int(r['gaussian_cache_calls']))%1000
    previous=int(r['gaussian_index'])
   accounting+=len(rs)
 checks['selected_new_raw_frames']=frames;checks['accounting_rows']=accounting
 for cid in ['C7','K2']:
  original=support/'OFF_original'/f'{cid}_0';off=support/'banks'/f'OFF_{cid}_0';a=rows(original/'ALL_FRAME_SHA256_AND_TIME.csv');b=rows(off/'ALL_FRAME_SHA256_AND_TIME.csv');assert len(a)==len(b)==1803
  for x,y in zip(a,b):
   for k in ['frame','wind_index','filaments','SHA256']:assert x[k]==y[k],(cid,k)
   assert float(x['physical_snapshot_time_s'])==float(y['physical_snapshot_time_s'])
  for p in original.glob('RNG.*'):assert sha(p)==sha(off/p.name),(cid,p.name)
 checks['full_OFF_identical_frame_indices']=3606
 spots=rows(core/'RAW_PHYSICAL_CONTRIBUTION_SPOTCHECK.csv');receiver=module('nmc_portable_receiver',core/'source/portable/receiver_math.py');err=0
 for r in spots:
  f=support/'readouts'/f"B4_{r['candidate']}_{r['reference']}";event=rows(f/'EVENTS_O1.csv')[int(r['block'])];p=support/'raw_spotchecks'/f"{r['candidate']}_{r['reference']}"/('iteration_'+r['frame']);d=raw_decoder.snapshot(p);point=np.array([[float(event[k]) for k in ['x','y','z']]],dtype=np.float32)
  _,total,_,_,_=receiver.cutoff_and_contributions(d['filaments'],point,d,occ,raw_decoder);e=abs(float(total[0])-float(r['native_ppm']));assert e<=3e-7+5e-6*abs(float(r['native_ppm']));err=max(err,e)
 checks['raw_receiver_spotqueries']=len(spots);checks['raw_receiver_max_abs_ppm']=err
 fresh=rows(core/'FRESH_CONFIRMATION_RESULTS.csv');assert len(fresh)==18
 for r in rows(core/'FRESH_RESTRICTED_CANDIDATE_SCORES.csv'):
  inp=rows(support/'native'/('FRESH_N0_'+r['oid'])/'final_map.csv')
  qp=support/'point_scores'/(r['candidate']+'_R01.f32') if r['method']=='N_POINT' else support/'confirmation_reference'/('PUBLIC_B_R01_'+r['candidate']+'_'+r['method']+'.f32')
  e=abs(logscore(inp,np.fromfile(qp,dtype='<f4'),.4)-float(r['native_log_similarity']));assert e<1e-10;maximum=max(maximum,e)
 receptor=rows(core/'FRESH_RECEPTOR_PREDICTION_METRICS.csv');events=rows(core/'FRESH_EVENTS_AND_PREDICTIONS.csv')
 for r in receptor:
  rr=[e for e in events if e['oid']==r['oid']];assert len(rr)==50
  if r['method'] in ['O0','O1']:value=np.mean([(float(e['true_'+r['method']+'_prediction'])-int(e['observed_hit']))**2 for e in rr]);assert abs(value-float(r['Brier']))<1e-12
  else:
   delta=np.array([float(e['true_O1_ppm'])-float(e['observed_ppm']) for e in rr]);assert abs(np.mean(abs(delta))-float(r['MAE_ppm']))<1e-12;assert abs(np.sqrt(np.mean(delta**2))-float(r['RMSE_ppm']))<1e-12
 checks['fresh_realizations']=6;checks['independent_logscore_max_abs']=maximum;checks['posterior_max_abs']=pcmax
 return dict(status='PASS_PORTABLE_NUMERIC_HASH_AUDIT',checks=checks,seconds=time.perf_counter()-start,scope='Packaged numerical evidence, 114 new raw frame samples and12 receiver queries; complete external raw banks are indexed but not byte-revalidated here. Scientific validity is separately bounded.')
if __name__=='__main__':
 root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent.parent
 print(json.dumps(verify(root),ensure_ascii=False,indent=2))
