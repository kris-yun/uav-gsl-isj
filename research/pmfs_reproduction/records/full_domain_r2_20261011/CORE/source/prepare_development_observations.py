"""Old observed material only; labels are written solely to evaluation_only."""
from common_r2 import *
import csv,numpy as np,shutil
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
infer=CORE/'inference_inputs';infer.mkdir();obs=[];truth={};parent_truth=load(R1/'evaluation_only/PUBLIC_TASK_TRUTH.json');source=load(CORE/'SOURCE_CATALOG_AND_COVERAGE.json');mapping=np.load(CORE/'SOURCE_CELL_TO_REGION.npy',allow_pickle=False)
def region(xyz):
 i=int(np.float32((np.float32(xyz[0])-np.float32(-7.55))/.25));j=int(np.float32((np.float32(xyz[1])-np.float32(-7.88))/.25));cell=i+34*j;assert mapping[cell]>=0;return cell,int(mapping[cell])
for oid,tr in parent_truth.items():
 run=R1RAW/'support/native'/('N0_'+oid);ev=rows(R1/f'native_inputs/events/{oid}.csv');xyz=tr['source_xyz'];obs.append(dict(oid=oid,plan='PUBLIC_B',events=ev,run=run,source=tr['candidate'] if 'candidate' in tr else tr.get('source_id',''),xyz=xyz,role='already_seen_PUBLIC_B'))
future_parent=load(R1/'FRESH_CONFIRMATION_PREREGISTRATION.json')
for j in future_parent['jobs']:
 oid=j['oid'];run=R1RAW/'support/native'/('FRESH_N0_'+oid);ev=rows(R1/f'native_inputs/events/{oid}.csv');obs.append(dict(oid=oid,plan='PUBLIC_B',events=ev,run=run,source=j['candidate'],xyz=j['source_xyz'],role='already_seen_R1_X_material'))
original=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/runtime/updates';ev=rows(CORE/'registered_covariates/B4_plan.csv');obs.append(dict(oid='B4',plan='B4',events=ev,source='C7',xyz=[-3.2,-3.3,-.5],role='frozen_original_B4_Action'))
registry=[]
for ob in obs:
 oid=ob['oid'];folder=infer/'observations'/oid;folder.mkdir(parents=True);bundle={};baseline={};cell,reg=region(ob['xyz'])
 source_name=ob['source'] or ('B000' if oid[-2:] in ['00','01'] else 'B001' if oid[-2:] in ['02','03'] else 'B002')
 truth[oid]=dict(source_group=source_name,source_xyz=ob['xyz'],source_cell=cell,true_region=reg,role=ob['role'],continuous_ppm_available=oid!='B4')
 for prefix in [20,35,50]:
  wc(folder/f'EVENTS_{prefix}.csv',ob['events'][:prefix])
  if oid=='B4':
   u=original/('update_'+str([20,35,50].index(prefix)));mr=rows(u/'input.csv');post=np.fromfile(u/'posterior.f64',dtype='<f8')
  else:mr=rows(ob['run']/f'map_blocks_{prefix}.csv');post=np.fromfile(ob['run']/('update_'+str([20,35,50].index(prefix)))/'posterior.f64',dtype='<f8')
  wc(folder/f'GRID_INPUT_{prefix}.csv',mr)
  bundle[f'p{prefix}']=np.array([float(r['probability']) if 'probability' in r else 1/(1+np.exp(-float(r['logOdds']))) for r in mr],float);bundle[f'c{prefix}']=np.array([float(r['confidence']) for r in mr],float);baseline[f'p{prefix}']=post
 np.savez_compressed(folder/'MEASURED_MAPS.npz',**bundle);np.savez_compressed(folder/'N0_FROZEN_POSTERIORS.npz',**baseline)
 registry.append(dict(oid=oid,plan=ob['plan'],folder='observations/'+oid,role='development_already_seen',truth_fields_in_consumer_files=False))
dump(infer/'OBSERVATION_REGISTRY.json',registry);dump(CORE/'evaluation_only/DEVELOPMENT_TRUTH.json',truth);shutil.copy2(CORE/'SOURCE_CATALOG_AND_COVERAGE.json',infer/'SOURCE_CATALOG.json');shutil.copy2(CORE/'SOURCE_CELL_TO_REGION.npy',infer/'SOURCE_CELL_TO_REGION.npy')
grid=rows(R1/'native_inputs/inputs/DERIVED/input.csv');free=np.array([r['occupancy']=='1' for r in grid]);np.save(infer/'SCORING_FREE_MASK.npy',free,allow_pickle=False)
dump(CORE/'DEVELOPMENT_GATE_PREREGISTRATION.json',dict(primary='P3-O1 minus P3-O0 source-region NLL, same coarsecatalog/prior/nativehead, R01, block50',enter_future='input/cov/support complete; mean sourceNLL improves and >=2oldsource groups improve; equal-source-group mean nativeTop5 distance notworse at numerical1e-10 tolerance',no_artificial_1m_gate=True,rescue_harm_all_reported=True,source_unit='Known oldsource group, observation realization; correlatedblocks notindependent',future_confirmation='Six allretained; mean sourceNLL improves, >=2of3newsourcegroups improve, meanTop5 notworse, no newwrongMAPregioncase hiddenbymean',helper_heads='E-event/A1 descriptive; no crossheadNLL percentage comparisons',no_future_if_development_fails=True,no_new_seed_if_confirmation_fails=True))
dump(CORE/'OBSERVATION_STAGING_AND_LABEL_SEPARATION.json',dict(status='PASS_REGISTRIES_SEPARATED',observations=len(registry),future_observations_not_opened=True,prefix_files=[20,35,50],B4_concentration_placeholder='Use frozenbinaryhits/map only; continuous PPManalysis onB4 deferred untilactual rawblocklog is available; zero placeholders nottreated aszero concentration'))
print(json.dumps({'status':'DEVELOPMENT_OBSERVATIONS_STAGED','count':len(registry),'truth_not_in_inference_inputs':True}))
