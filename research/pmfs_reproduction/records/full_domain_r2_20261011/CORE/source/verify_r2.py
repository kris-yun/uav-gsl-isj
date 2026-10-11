"""Read-only portable R2 audit: no SSH/VM/ROS, no new physics or posterior update.
Usage: python -B source/verify_r2.py --core CORE [--raw RAW]
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,json,csv,hashlib,time,math
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from source_map_tools import validate_partition,contract_diff,native_log_score
from infer_source_matrix import calculate
import raw_decode as raw
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8',newline='')))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def verify(core,rawroot=None):
 start=time.perf_counter();manifest=load(core/'MANIFEST_SHA256.json');hashes=0
 assert set(manifest)=={p.relative_to(core).as_posix() for p in core.rglob('*') if p.is_file() and p!=core/'MANIFEST_SHA256.json'},'CORE manifest incomplete coverage'
 for name,v in manifest.items():assert sha(core/name)==v,name;hashes+=1
 cat=load(core/'SOURCE_CATALOG_AND_COVERAGE.json')['catalog'];ids=np.load(core/'SOURCE_CELL_TO_REGION.npy');mask=ids>=0;counts=validate_partition(ids,mask,32);assert mask.sum()==447 and np.array_equal(counts,np.array([c['cell_count'] for c in cat]));assert np.allclose(np.array([c['prior'] for c in cat]),counts/447,atol=1e-15)
 objects=0;diff=0;truthcheck=0
 for prefix,folder,trfile,csvfile in [('','development_inference','DEVELOPMENT_TRUTH.json','PAIRED_SOURCE_METRICS.csv'),('future_','future_inference','FUTURE_TRUTH.json','FUTURE_PAIRED_SOURCE_METRICS.csv')]:
  root=core/(prefix+'inference_inputs');saved=np.load(core/folder/'FULL_SOURCE_POSTERIORS.npz',allow_pickle=False);truth=load(core/'evaluation_only'/trfile);metrics={r['key']:r for r in rows(core/csvfile)}
  assert sha(root/'ALL_CANDIDATE_PREDICTIONS.npz')==load(core/'PREDICTOR_LIBRARY_FREEZE.json')['sha256']
  for n in [20,35,50]:
   rs,_=calculate(root,n)
   for r in rs:
    key=f'{r["oid"]}__{r["group"]}__{r["method"]}__{n}';objects+=1
    for k,z in [('scores','log_scores'),('weights','source_weights'),('posterior','posterior')]:diff=max(diff,float(np.max(abs(saved[key+'_'+k]-r[z]))))
    assert abs(r['posterior'].sum()-1)<1e-12 and (r['posterior'][~mask]==0).all();t=truth[r['oid']];w=r['source_weights'][t['true_region']];assert abs(float(metrics[key]['source_region_NLL'])+math.log(w))<1e-12;truthcheck+=1
 assert objects==1125 and diff<1e-12
 pairs=rows(core/'FUTURE_READOUT_PAIRED_EFFECTS.csv');p50=[r for r in pairs if r['blocks']=='50'];decision=load(core/'FUTURE_CONFIRMATION_DECISION.json');assert len(p50)==6 and abs(np.mean([float(r['NLL_delta_O1_minus_O0']) for r in p50])-decision['mean_region_NLL_delta'])<1e-12;assert decision['status']=='DESCRIPTIVE_CONFIRMATION_NOT_MET_END_THIS_CONSTRUCTION' and decision['source_equal_mean_nativeTop5_delta']>0
 blind=load(core/'BLINDING_AND_PREFIX_TESTS.json');assert blind['status']=='PASS' and len(blind['tests'])==7;native=load(core/'NATIVE_SCORING_AND_METRIC_VALIDATION.json');assert native['score_maps']==576 and native['max_log_score_difference']<1e-10
 con=load(core/'PAIR_CONTRACT_DIFF.json');contract_diff(con['O0'],con['O1'],allowed_paths=('readout',));assert con['changed_paths']==['readout']
 rawhash=physical=queries=native_candidates=native_updates=0;maxppm=maxnative=0
 if rawroot is not None:
  assert set(load(rawroot/'MANIFEST_SHA256.json'))=={p.relative_to(rawroot).as_posix() for p in rawroot.rglob('*') if p.is_file() and p!=rawroot/'MANIFEST_SHA256.json'},'RAW manifest incomplete coverage'
  for name,v in load(rawroot/'MANIFEST_SHA256.json').items():assert sha(rawroot/name)==v,name;rawhash+=1
  occ=raw.occupancy(core/'geometry/OccupancyGrid3D.csv')
  for role in ['references','observations']:
   for bank in sorted((rawroot/role).iterdir()):
    qual=load(bank/'QUALIFICATION.json');assert qual['status']=='PASS_PHYSICAL_REFERENCE_AND_NATIVE_READOUT';assert sha(bank/'PREDICTIONS.npz')==qual['predictions_SHA256'];a=np.load(bank/'PREDICTIONS.npz');idx={int(r['frame']):r for r in rows(bank/'ALL_FRAME_SHA256_AND_TIME.csv')};assert len(idx)==1803
    for f in sorted((bank/'used_frames').iterdir()):
     frame=int(f.name.split('_')[1]);assert sha(f)==idx[frame]['SHA256'];desc=raw.snapshot(f);assert desc['gas_type']==13 and np.array_equal(desc['source'],np.array(qual['source_xyz'],np.float32));assert raw.cell_state(desc['source'],desc,occ)==0;physical+=1
    # Fixed first/last actual receptor at each bank: independent decode, LOS and float32 PID math.
    for plan in ['B4','PUBLIC_B']:
     events=rows(bank/(plan+'_RECEIVER_EVENTS.csv'));line=rows(bank/(plan+'_FRAME_LINEAGE.csv'))
     for b in [0,49]:
      r=line[b];frame=int(r['frame']);assert float(r['selected_physical_s'])<=float(r['target_physical_s'])<float(r['next_frame_physical_s']);assert int(r['wind_index'])==10;desc=raw.snapshot(bank/'used_frames'/f'iteration_{frame}');e=events[b];xyz=[float(e[k]) for k in ['x','y','z']];value,_=raw.concentration(xyz,desc,occ);expected=np.float32(a[plan+'_receiver_ppm'][b]);err=abs(float(value)-float(expected));maxppm=max(maxppm,err);assert err<=raw.ATOL+raw.RTOL*abs(float(expected));assert (value>np.float32(.1))==(expected>np.float32(.1));queries+=1
  for bank in sorted((rawroot/'observations').iterdir()):
   first=rows(bank/'N0/update_0/candidates.csv')[0];assert first['gaussian_ready_before']=='0' and first['rng_before']=='470211272'
   for d in sorted((bank/'N0').glob('update_*')):
    if not d.is_dir():continue
    grid=rows(d/'input_full.csv');p=np.array([float(r['probability']) for r in grid]);c=np.array([float(r['confidence']) for r in grid]);qrows=rows(d/'candidates.csv');qs=np.stack([np.fromfile(d/r['map_file'],dtype='<f4') for r in qrows]);s=native_log_score(p,c,qs,mask,.4);expected=np.array([float(r['logscore']) for r in qrows]);maxnative=max(maxnative,float(np.max(abs(s-expected))));assert np.max(abs(s-expected))<1e-10;native_candidates+=len(qrows)
    rawcell=np.array([float(r['score']) for r in rows(d/'raw_cell_scores.csv')]);post=np.fromfile(d/'posterior.f64',dtype='<f8');normal=float((d/'normalization.txt').read_text());assert abs(rawcell[mask].sum()-normal)<1e-10*max(1,normal);normalized=np.where(mask,rawcell/normal,0);assert np.max(abs(normalized-post))<1e-12;native_updates+=1
  assert native_candidates==2286 and native_updates==18
 return dict(status='PASS_PORTABLE_R2_RECOMPUTATION',core_hashes=hashes,raw_hashes=rawhash,ordinary_source_posteriors=objects,max_source_recompute_difference=diff,true_source_losses=truthcheck,raw_used_frames=physical,independent_PID_queries=queries,max_PID_absolute_ppm_difference=maxppm,new_actual_native_candidate_scores=native_candidates,new_actual_native_updates=native_updates,max_native_candidate_logscore_difference=maxnative,all_zero_positive_negative_banks_retained=True,wall_s=time.perf_counter()-start,scope='Frozen32source/447cells, twofinite references, noROSAction ornewphysics verification; nativeTop5/C++ties recorded separately')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--raw',type=Path);a=p.parse_args();print(json.dumps(verify(a.core,a.raw),ensure_ascii=False,indent=2))
