from common_r2 import *
import numpy as np,csv,shutil
cat=load(CORE/'SOURCE_CATALOG_AND_COVERAGE.json')['catalog'];ref=load(HOST/'REFERENCE_LEDGER.json');point=load(HOST/'N_POINT_ALL_LEDGER.json')
assert ref['status'].startswith('PASS') and len(ref['records'])==64 and point['status'].startswith('PASS')
out={};evidence=[]
for plan in ['B4','PUBLIC_B']:
 for key in ['EVENTS','PPM']+[f'{m}_{n}' for n in [20,35,50] for m in ['P3-O0','P3-O1','A1']]:out[plan+'_'+key]=[]
 out[plan+'_AUX']=[]
for source in cat:
 banks=[]
 for rep in [0,1]:
  folder=HOST/'references'/f'{source["source_id"]}_REF{rep}';q=load(folder/'QUALIFICATION.json');assert q['status']=='PASS_PHYSICAL_REFERENCE_AND_NATIVE_READOUT' and sha(folder/'PREDICTIONS.npz')==q['predictions_SHA256']
  banks.append(np.load(folder/'PREDICTIONS.npz',allow_pickle=False));evidence.append(dict(id=q['id'],qualification_sha=sha(folder/'QUALIFICATION.json'),predictions_sha=q['predictions_SHA256'],all_frame_index_sha=sha(folder/'ALL_FRAME_SHA256_AND_TIME.csv'),frames=q['raw_frames'],retained=q['used_raw_frames']))
 for plan in ['B4','PUBLIC_B']:
  out[plan+'_EVENTS'].append(np.stack([b[plan+'_receiver_events'] for b in banks]));out[plan+'_PPM'].append(np.stack([b[plan+'_receiver_ppm'] for b in banks]))
  out[plan+'_AUX'].append(np.stack([b['PUBLIC_B_auxiliary'] for b in banks]) if plan=='PUBLIC_B' else np.zeros((2,50,0,5),np.float32))
  for n in [20,35,50]:
   for method,bkey in [('P3-O0',f'{plan}_O0_{n}_blurred'),('P3-O1',f'{plan}_O1_{n}_blurred'),('A1',f'{plan}_A1_{n}')]:out[f'{plan}_{method}_{n}'].append(np.stack([b[bkey] for b in banks]))
 for b in banks:b.close()
out={k:np.stack(v) for k,v in out.items()};out['N_POINT_ALL']=[]
for source in cat:
 maps=[]
 for group in ['R0','R1']:
  d=HOST/'N_POINT_ALL'/group/source['source_id']/'forward';row=list(csv.DictReader((d/'candidates.csv').open()))[0];a=np.fromfile(d/row['map_file'],dtype='<f4');assert a.shape==(1530,);maps.append(a)
 out['N_POINT_ALL'].append(np.stack(maps))
out['N_POINT_ALL']=np.stack(out['N_POINT_ALL']);p=CORE/'inference_inputs/ALL_CANDIDATE_PREDICTIONS.npz';assert not p.exists();np.savez_compressed(p,**out)
dump(CORE/'PREDICTOR_LIBRARY_FREEZE.json',dict(status='PASS_ALL32_REGIONS_64_REFERENCES_64_NATIVE_POINT_CALLS',sha256=sha(p),shapes={k:list(v.shape) for k,v in out.items()},averaging='R01 mean predictor first then score; average already-native-blurred reference fields, same order O0/O1',source_count=32,covered_source_cells=447,receiver_scoring_cells=447,reference_replicates_per_source=2,query_rows_per_reference=45000,queries_total=2880000,source_labels_not_consumed=True,evidence=evidence))
for name in ['REFERENCE_LEDGER.json','N_POINT_ALL_LEDGER.json']:shutil.copy2(HOST/name,CORE/name)
shutil.copy2(WORK/'pro_plan/code/source_map_tools.py',CORE/'source/source_map_tools.py')
shutil.copy2(WORK/'infer_source_matrix.py',CORE/'source/infer_source_matrix.py')
print(json.dumps({'status':'PASS_PREDICTOR_LIBRARY_FROZEN','bytes':p.stat().st_size}))
