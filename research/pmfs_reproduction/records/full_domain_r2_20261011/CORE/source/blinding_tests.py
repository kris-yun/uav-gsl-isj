from common_r2 import *
import numpy as np,shutil,sys
sys.path.insert(0,str(WORK/'pro_plan/code'));from infer_source_matrix import calculate
root=CORE/'inference_inputs';base=WORK/'blind_tests';base.mkdir();clean=base/'minimal_no_truth';clean.mkdir();registry=load(root/'OBSERVATION_REGISTRY.json')
for n in ['SOURCE_CATALOG.json','SCORING_FREE_MASK.npy','SOURCE_CELL_TO_REGION.npy','ALL_CANDIDATE_PREDICTIONS.npz','OBSERVATION_REGISTRY.json']:shutil.copy2(root/n,clean/n)
for ob in registry:
 dest=clean/ob['folder'];dest.mkdir(parents=True)
 for n in ['MEASURED_MAPS.npz','EVENTS_20.csv','EVENTS_35.csv','EVENTS_50.csv']:shutil.copy2(root/ob['folder']/n,dest/n)
expected={n:calculate(root,n)[0] for n in [20,35,50]};checks=[]
def compare(label,result,n,perm=None):
 maxerr=0
 for a,b in zip(expected[n],result):
  for key in ['posterior','source_weights','log_scores']:
   x=b[key]
   if perm is not None and key!='posterior':x=x[np.argsort(perm)]
   maxerr=max(maxerr,float(np.max(abs(x-a[key]))))
 assert maxerr<1e-12;checks.append(dict(test=label,blocks=n,objects=len(result),max_difference=maxerr,status='PASS'))
for n in [20,35,50]:compare('hidden_data_deleted_and_no_true_source_mapping',calculate(clean,n)[0],n)
renamed=base/'renamed_permuted_candidates';shutil.copytree(clean,renamed);perm=np.arange(31,-1,-1);cat=load(renamed/'SOURCE_CATALOG.json');cat['catalog']=[dict(cat['catalog'][int(i)],source_id=f'ANON_{j:03}',source_index=j) for j,i in enumerate(perm)];dump(renamed/'SOURCE_CATALOG.json',cat);pred=np.load(clean/'ALL_CANDIDATE_PREDICTIONS.npz');np.savez_compressed(renamed/'ALL_CANDIDATE_PREDICTIONS.npz',**{k:pred[k][perm] for k in pred.files});ids=np.load(clean/'SOURCE_CELL_TO_REGION.npy');inv=np.argsort(perm);ids[ids>=0]=inv[ids[ids>=0]];np.save(renamed/'SOURCE_CELL_TO_REGION.npy',ids)
for n in [20,35,50]:compare('candidate_renaming_and_permutation_equivariance',calculate(renamed,n)[0],n,perm)
past=base/'prefix20_future_deleted';shutil.copytree(clean,past)
for ob in registry:
 d=past/ob['folder'];m=np.load(d/'MEASURED_MAPS.npz');keep={k:m[k] for k in ['p20','c20']};m.close();np.savez_compressed(d/'MEASURED_MAPS.npz',**keep)
 for name in ['EVENTS_35.csv','EVENTS_50.csv']:(d/name).unlink()
pp={k:pred[k][:,:,:20] if k.endswith(('EVENTS','PPM','AUX')) else pred[k] for k in pred.files if not k.endswith(('_35','_50'))};np.savez_compressed(past/'ALL_CANDIDATE_PREDICTIONS.npz',**pp);compare('prefix20_no_future_observations_or_prediction_summaries',calculate(past,20)[0],20)
reads=[]
def audit(event,args):
 if event=='open' and isinstance(args[0],str):reads.append(args[0])
sys.addaudithook(audit);calculate(clean,50);opened=sorted(set(reads));assert all(str(clean) in p for p in opened),opened
dump(CORE/'BLINDING_AND_PREFIX_TESTS.json',dict(status='PASS',tests=checks,consumer_opened_files=opened,consumer_no_truth_or_particle_bank_access=True,minimal_tree_files=sum(p.is_file() for p in clean.rglob('*')),labels_deleted_before_actual_inference=True,raw_N0_and_GRID_not_needed_by_inference=True,source_id_names_not_used_as_features=True))
print(json.dumps({'status':'PASS_BLINDING_AND_PREFIX','tests':len(checks)}))
