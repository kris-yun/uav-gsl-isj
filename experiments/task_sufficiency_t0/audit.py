"""Hash selected native inputs, inspect contracts, and freeze training operational details."""
import hashlib,json,shutil
from pathlib import Path
import pandas as pd,numpy as np
O=Path(__file__).resolve().parents[2]/'evidence/task_sufficiency_t0_20261003'
OLD=Path(r'D:\ZYC\A-gas\_worktrees\mdbil-d0-20261001\evidence\ocb_r2')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 runs=json.loads((O/'RUNS.json').read_text());records=[];qa=[]
 for r in runs:
  folder=Path(r['folder']); orig=OLD/('s2_runs' if r['phase']=='S2' else 's2x/runs'); meta=O/'provenance'/r['run_id'];meta.mkdir(parents=True,exist_ok=True)
  for suffix in ['RUN_MANIFEST.json','QC.json','ARCHIVE_PROOF.json','FULL_SHA256SUMS.txt']:
   p=orig/(r['run_id']+'.'+suffix);shutil.copyfile(p,meta/suffix)
  shutil.copyfile(folder/'RECORD_TIMELINE.tsv',meta/'RECORD_TIMELINE.tsv')
  inventory={line.split('  ',1)[1].replace('\\','/'):line.split('  ',1)[0] for line in (meta/'FULL_SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines() if '  ' in line}
  route=pd.read_csv(O/(r['run_id']+'.route.csv'));obs=pd.read_csv(O/(r['run_id']+'.observations.csv'));timeline=pd.read_csv(meta/'RECORD_TIMELINE.tsv',sep='\t')
  assert np.array_equal(obs.record_index,route.record_index) and np.allclose(obs[['x','y','z']],route[['x','y','z']],atol=1e-6)
  age=obs.time.values-timeline.internal_simulation_time_s.values[obs.record_index.values];assert np.min(age)>=0 and np.max(age)<1
  assert np.isfinite(obs.values).all() and (obs.concentration>=0).all()
  for p in [folder/f'iteration_{i}' for i in set(route.record_index)]+list((folder/'wind').iterdir()):
   h=sha(p);rel=p.relative_to(folder).as_posix();matching=[v for k,v in inventory.items() if k==rel or k.endswith('/'+rel)];assert matching and all(v==h for v in matching),(rel,list(inventory)[:3]);records.append(dict(run_id=r['run_id'],path=str(p),relative_path=rel,bytes=p.stat().st_size,sha256=h))
  qa.append(dict(run_id=r['run_id'],context=r['context'],source_id=r['source_id'],master_seed=r['master_seed'],samples=len(obs),hit_fraction=float((obs.concentration>=.001).mean()),peak_ppm=float(obs.concentration.max()),max_record_age_s=float(age.max())))
 pd.DataFrame(records).to_csv(O/'NATIVE_INPUT_SHA256.csv',index=False);pd.DataFrame(qa).to_csv(O/'OBSERVATION_QA.csv',index=False)
 for c in {r['context'] for r in runs}:
  rr=[r for r in runs if r['context']==c];assert len(rr)==8 and len({r['source_id'] for r in rr})==2
  assert len({json.loads((Path(r['folder'])/'RUN_MANIFEST.json').read_text())['asset_checks']['wind_bundle_sha256'] for r in rr})==1
 p=json.loads((O/'PROTOCOL_FROZEN.json').read_text());p.update(model_initialization_seeds=[61003,61004,61005],nuisance_probe='conditional on source, classify the THREE training-realization IDs; early history end<=300s vs late>=440s; temporally disjoint spans; chance1/3; this is seen-ID temporal extrapolation diagnostic, not unseen-ID classification',history_sampling='20 observations at2s cadence, 38s endpoint span within nominal40s history budget',source_readout='same L2 logistic regression C=1 on train-standardized arm representation; rank/AUC from equal-weight mean probabilities per heldout complete realization; neural init seeds averaged',prediction_readout='identical linear logistic/ridge heads using representation and known future XYZ; no future wind/gas input',gate_interpretation='source-rank versus raw; AUC median case gain; mean Brier AND hit NLL at pooled10/30 improve over source-only; mean nuisance accuracy strictly lower than generic; source-probe mean>=.75; all operationalizations before model fitting',bottleneck='8 continuous latent coordinates; L2 penalty is a regularizer, not a certified information bound',route_limitation='one connected component, one low indoor height, two-source feasibility only; not a true UAV flight or full 3D shape reconstruction',comparison_statistics='54 windows per realization are correlated; effective sample size8 realizations/case, not432 windows')
 (O/'PROTOCOL_FROZEN.json').write_text(json.dumps(p,indent=2)+'\n');(O/'PRE_TRAIN_FREEZE_SHA256.txt').write_text(sha(O/'PROTOCOL_FROZEN.json')+'  PROTOCOL_FROZEN.json\n'+sha(Path(__file__).parent/'train.py')+'  train.py\n')
 print('native byte verification PASS; preprocessing/training protocol frozen',flush=True)
if __name__=='__main__':main()
