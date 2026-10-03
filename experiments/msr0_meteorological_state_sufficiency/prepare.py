"""Read-only audit and native replay of existing 64 qualified S2/S2X realizations."""
from pathlib import Path
import json,hashlib,subprocess,shlex,tarfile,itertools,shutil,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'evidence/msr0_meteorological_state_sufficiency_20261003';OUT.mkdir(parents=True,exist_ok=True)
LOCAL=Path('C:/work/MSR0_METEOROLOGICAL_STATE_SUFFICIENCY_20261003');LOCAL.mkdir(exist_ok=True)
OLD=Path('D:/ZYC/A-gas/_worktrees/mdbil-d0-20261001');T0=ROOT/'evidence/task_sufficiency_t0_20261003'
ARCH=Path('C:/GADEN_OCB_R2_ARCHIVE');HOST='zyc@192.168.111.128';REM='/dev/shm/msr0_met_state_sufficiency_20261003'
EXPECTED='ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def run(a):
 p=subprocess.run(a,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(str(a)+'\n'+p.stderr[-4000:])
 return p.stdout
def ssh(cmd):return run(['ssh','-o','ConnectTimeout=15','-o','BatchMode=yes',HOST,cmd])
def scp(p,target):run(['scp','-q',str(p),target])
ENV='source /opt/ros/humble/setup.bash && export LD_LIBRARY_PATH=/home/zyc/ocb_r2_seeded_gaden/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH && '

config={'experiment':'MSR0_METEOROLOGICAL_STATE_SUFFICIENCY','base_commit':run(['git','rev-parse','HEAD']).strip(),
 'primary_cases':{'H01/s0':0,'H01/s1':2,'H02/s0':4,'H02/s1':6},'audit_all_existing_configs':list(range(8)),
 'no_new_gaden_before_alias_gate':True,'no_neural_network':True,'no_old_gate_edits':True,
 'path':'Reuse frozen source-blind T0 route separately for each House, identical301 receptor points/times100..700s step2s in every context and source. Not an actual UAV route.',
 'geometry_contract':'Never compare different houses as meteorology-only interventions. Match sourceXYZ, gas type, release/growth/noise/thermodynamics/generator/timeline across wind contexts.',
 'Phi0':'Native full-free-floor UV wind slice (stronger spatial resolution than coarse PMFS; same information class, not algorithm reproduction) plus UV at fixed receptor locations; PMFS code actually supports spatial2D wind map, never replace it by a flight mean.',
 'Phi1':'Phi0 plus receptor W only',
 'Phi2':'Phi1 plus central differences across fixed z offsets[-.2,+.2]m: vector derivative, shortest directional difference, speed difference. Missing/obstructed cells are masked identically across contexts, not imputed zeros.',
 'Phi3':'Phi2 plus gradients alongx/y offsets[-.2,+.2]m and central local-neighbor directional concentration and speed SD. Spatial variability, NOT TKE/turbulence.',
 'Phi_ORACLE':'Phi3 plus fixed3x3x3 patch offsets[-.4,0,.4]m around each receptor, mask fixed by geometry. Oracle not deployable algorithm.',
 'feature_blindness':'wind_query executable accepts only occupancy,wind files,source-blind receptor probes. Never source coordinates,gas headers or truth for feature/weight construction.',
 'wind_state_semantics':'Use11 saved wind states and recorded wind-index sequence for mapping observation times. CFD-state physical temporal meaning unproven: no turbulence/TKE/frequency inference from index.',
 'distance':'Symmetric relative RMS per block = RMS(a-b)/sqrt((RMS(a)^2+RMS(b)^2)/2),zero-scale identical block ->0. Phi distance =equal-block RMS; nested representations not rawdimension dominated.',
 'Phi0_primary_distance':'Full2D-slice block plus receptorUV block, equal weight, weighted states by fixed route wind-index counts.',
 '2D_close_threshold':.10,'2D_close_sensitivity':[.05,.20],'closeness_basis':'Engineering relative meteorology proximity frozen before gas scoring, not an absolute gas/noise gate. Also report unconstrained nearest neighbors, never force a nearest pair to be close.',
 'gas_distance':'RMS difference of log1p(ppm) on identical301 time/space sample trace. Additional normalized shape distance descriptive only. No per-trace rescaling in primary.',
 'within_floor':'All6 pairs of4 whole independent realizations per context/source. Context-pair/source floor=q95 pooling12 within distances from both contexts; report median/q90/q95 separately. Shared pair endpoints not independent sample inflation.',
 'alias_gate':'Legal matched pair, Phi0<=.10, median of16 between-seed gas distances > pooled within q95, AND ensemble-mean trace difference>same q95. Report ratio and each source separately; no absolute JSD gate.',
 'representation_metrics':'Same legal context pairs for allPhi; Spearman on context-level mean across sources descriptive due only4 legal interventions; nearest-neighbor gas mismatch/noise ratio and false neighbors. Context retrieval uses matched nonself eligible contexts; one-candidate cases marked unidentifiable, not100% accuracy.',
 'localization_only_after_alias':'Use matched existing bank, whole-realization leave-one-context-out and leave-one-house-out only if transferable geometry support is proved; do not silently treat2-source classification as continuous-grid localization.',
 'retrieval_rule_if_gate_passes':'Equal-prior mixture over compatible training contexts, exp(-distance^2/median_positive_train_distance^2), scale computed on training contexts only; profile nonnegative amplitude likelihood with training-within stochastic scale, fixed prior over candidates. No truth-based weights.',
 'localization_engineering_gate':{'median_meter_error_gain_min':.15,'case_direction_min':'3/4','each_source':'no systematic decline','paired_context_bootstrap':'must not show clear opposite direction; very small context count disclosed','Phi2_or_Phi3_vs_oracle':'at least80% of oracle positive median error gain'},
 'gate_dependencies':'Only alias PASS permits minimal missing source bank; only useful lowdim representation+coordinate benefit permits Wisco bridge. If no alias, STOP scoped to current data/route. Missing scientific identification marked NOT_ESTABLISHED, never proof of universal2D sufficiency.'}
if not(OUT/'MSR0_FROZEN_CONFIG.json').exists():save('MSR0_FROZEN_CONFIG.json',config)
else:
 frozen=json.loads((OUT/'MSR0_FROZEN_CONFIG.json').read_text(encoding='utf-8'));config['base_commit']=frozen['base_commit']
 assert frozen==config,'Frozen config changed'
save('PRE_SCORE_FREEZE.json',{'config_sha256':sha(OUT/'MSR0_FROZEN_CONFIG.json'),'prepare_code_sha256':sha(__file__),'wind_code_sha256':sha(CODE/'wind_query.cpp')})

resume='--resume' in sys.argv
runs=json.loads((OUT/'RUNS.json').read_text(encoding='utf-8')) if resume else []
inputs=pd.read_csv(OUT/'INPUT_SHA256.csv').to_dict('records') if resume else [];contracts=[]
phases=[('S2',OLD/'evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'),('S2X',OLD/'evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv')]
for phase,rl in ([] if resume else phases):
 inputs.append({'path':str(rl),'sha256':sha(rl),'role':'frozen_runlist'})
 for record in pd.read_csv(rl,sep='\t').to_dict('records'):
  ci=int(record['config_index'] if phase=='S2' else record['parent_s2_config_index']);rid=record['run_id'];folder=ARCH/('s2_discovery' if phase=='S2' else 's2x_matched_source')/rid
  m=json.loads((folder/'RUN_MANIFEST.json').read_text());assert m['generator_binary_sha256']==EXPECTED
  assert m['qualification_standard']['manifest_pass'] and m['qualification_standard']['scientific_sanity_pass']
  house=m['house'];context=f'{house}_cfg{ci:02d}';params=m['simulation_parameters']
  truth=[float(params['source_position_'+ax]) for ax in 'xyz']
  timeline=pd.read_csv(folder/'RECORD_TIMELINE.tsv',sep='\t');clock=np.arange(100,701,2);idx=np.searchsorted(timeline.internal_simulation_time_s,clock,side='right')-1;assert idx.min()>=0
  route=pd.read_csv(T0/(house+'_route.csv'));assert len(route)==301
  route.insert(0,'record_index',idx);route.insert(0,'time',clock);route.to_csv(OUT/(rid+'.route.csv'),index=False)
  meta=OUT/'provenance'/rid;meta.mkdir(parents=True,exist_ok=True)
  for name in ['RUN_MANIFEST.json','RECORD_TIMELINE.tsv','OUTPUT_SHA256SUMS.tsv']:
   src=folder/name;shutil.copyfile(src,meta/name);inputs.append({'run_id':rid,'path':str(src),'sha256':sha(src),'role':'metadata'})
  proofbase=OLD/'evidence/ocb_r2'/('s2_runs' if phase=='S2' else 's2x/runs')
  full=proofbase/(rid+'.FULL_SHA256SUMS.txt');qc=proofbase/(rid+'.QC.json');assert json.loads(qc.read_text())['decision']=='PASS'
  shutil.copyfile(full,meta/'FULL_SHA256SUMS.txt');shutil.copyfile(qc,meta/'QC.json')
  inputs.extend({'run_id':rid,'path':str(p),'sha256':sha(p),'role':'qualified_provenance'} for p in [full,qc])
  inventory={line.split('  ',1)[1].replace('\\','/'):line.split('  ',1)[0] for line in full.read_text(encoding='utf-8-sig').splitlines() if '  ' in line}
  selected=[folder/f'iteration_{k}' for k in sorted(set(idx))]+sorted((folder/'wind').glob('wind_iteration_*'))
  for p in selected:
   digest=sha(p);rel=p.relative_to(folder).as_posix();assert inventory[rid+'/'+rel]==digest
   inputs.append({'run_id':rid,'path':str(p),'sha256':digest,'bytes':p.stat().st_size,'role':'native_read_payload'})
  nsource={k:v for k,v in params.items() if k not in ['source_position_x','source_position_y','source_position_z','results_location','wind_data']}
  row={'run_id':rid,'config_index':ci,'context':context,'house':house,'phase':phase,'source_id':m['source_id'],'truth_xyz':truth,'seed':int(m['master_seed']),'folder':str(folder),'gas_type':params['gas_type'],'wind_bundle_sha256':m['asset_checks']['wind_bundle_sha256'],'occupancy_sha256':m['asset_checks']['occupancy_sha256'],'generator_sha256':EXPECTED,'timeline_sha256':sha(folder/'RECORD_TIMELINE.tsv'),'nonwind_nonsource_params':nsource,'wind_indices_at_receptors':timeline.wind_index.values[idx].astype(int).tolist(),'record_indices':idx.tolist()}
  runs.append(row);print('audited '+rid,flush=True)
assert len(runs)==64 and len({r['seed'] for r in runs})==64
save('RUNS.json',runs);pd.DataFrame(inputs).to_csv(OUT/'INPUT_SHA256.csv',index=False)
for ci in range(8):
 rr=[r for r in runs if r['config_index']==ci];assert len(rr)==8 and len({r['source_id'] for r in rr})==2
 assert len({r['wind_bundle_sha256'] for r in rr})==len({json.dumps(r['nonwind_nonsource_params'],sort_keys=True) for r in rr})==1
 contracts.append({'context':rr[0]['context'],'config_index':ci,'house':rr[0]['house'],'primary':ci in [0,2,4,6],'gas_type':rr[0]['gas_type'],'n_sources':2,'n_realizations_per_source':4,'n_receptors':301,'source_grid_compatible_bank':False,'bank_source_coordinates':[r['truth_xyz'] for r in rr if r['phase']=='S2' and r['seed']==min(x['seed'] for x in rr if x['phase']=='S2')]+[r['truth_xyz'] for r in rr if r['phase']=='S2X' and r['seed']==min(x['seed'] for x in rr if x['phase']=='S2X')],'wind3d_available':True,'full2d_slice_available':True})
save('MSR0_DATA_CONTRACT.json',{'contexts':contracts,'n_qualified_realizations':64,'metadata_FROZEN_NOT_RUN_runlist_label':'Superseded by actual QC PASS and archive byte proofs, not treated as execution status','candidate_bank':'Existing2-source prospective ensemble only. Arbitrary596/630 legacy candidates have generator/readout/time mismatch. No new forwards authorized at StageA.'})
bank=[]
for c in contracts:bank.append(dict(c,coverage_status='2_SOURCE_ONLY; NO_CONTINUOUS_GRID_BANK',full_grid_forward_fraction=None))
legacy=pd.read_csv(OLD/'evidence/ocb_r2/d0/D0A_EXISTING_BANK_AUDIT.tsv',sep='\t')
for x in legacy.to_dict('records'):bank.append({'context':x['bank'],'coverage_status':x['D0A_use'],'metadata_path':x['metadata_path'],'candidate_scope':x['candidate_scope']})
pd.DataFrame(bank).to_csv(OUT/'MSR0_FORWARD_BANK_COVERAGE.csv',index=False)
shutil.copyfile(OLD/'evidence/ocb_r2/d0/D0A_EXISTING_BANK_AUDIT.tsv',OUT/'LEGACY_BANK_AUDIT.tsv')

# Isolated read-only wind probes. Fixed coordinates and offsets, no source coordinates.
ssh('mkdir -p '+REM)
scp(CODE/'wind_query.cpp',HOST+':'+REM+'/wind_query.cpp')
build="""import pathlib,subprocess,shlex
b=pathlib.Path('/home/zyc/ocb_r2_seeded_gaden'); f=(b/'build/gaden_common/third_party/gaden_core/CMakeFiles/gaden.dir/flags.make').read_text().splitlines(); inc=next(x.split(' = ',1)[1] for x in f if x.startswith('CXX_INCLUDES')); lib=b/'install/gaden_common/lib'; bsc=b/'build/gaden_common/third_party/gaden_core/third_party/libbsc'
subprocess.run(['g++','-std=c++20','-O3','-DGADEN_ROS=1']+shlex.split(inc)+['REMOTE/wind_query.cpp','-L'+str(lib),'-Wl,-rpath,'+str(lib),'-Wl,-rpath,'+str(bsc),'-Wl,-rpath-link,'+str(bsc),'-lgaden','-o','REMOTE/wind_query'],check=True)
""".replace('REMOTE',REM)
(OUT/'build_wind.py').write_text(build,encoding='utf-8');scp(OUT/'build_wind.py',HOST+':'+REM+'/build_wind.py');ssh(ENV+'python3 '+REM+'/build_wind.py')
save('RUNTIME.json',{'libgaden_sha256':ssh('sha256sum /home/zyc/ocb_r2_seeded_gaden/install/gaden_common/lib/libgaden.so').split()[0],'wind_executable_sha256':ssh('sha256sum '+REM+'/wind_query').split()[0],'gas_query_sha256':ssh('sha256sum /home/zyc/task_sufficiency_t0_20261003/query').split()[0],'wind_adapter':'native WindSequence.GetCurrent + Environment.indexFrom3D; same as SampleWind; no gas files opened','gas_adapter':'Unchanged qualified T0 PlaybackSimulation query, no simulation started','physical_wind_state_duration':'not independently established from CFD; simulation state sequence recorded in timeline'})
for house in ['House01','House02']:
 free=pd.read_csv(T0/(house+'_free.csv'));route=pd.read_csv(T0/(house+'_route.csv'));probes=[]
 for xyz in free[['x','y','z']].values:probes.append({'kind':'slice','receptor':-1,'dx':0.,'dy':0.,'dz':0.,'x':xyz[0],'y':xyz[1],'z':xyz[2]})
 offsets=[(0.,0.,0.),(0.,0.,-.2),(0.,0.,.2),(-.2,0.,0.),(.2,0.,0.),(0.,-.2,0.),(0.,.2,0.)]+list(itertools.product([-.4,0.,.4],repeat=3))
 for j,xyz in enumerate(route[['x','y','z']].values):
  for off in dict.fromkeys(offsets):probes.append(dict(kind='local',receptor=j,dx=off[0],dy=off[1],dz=off[2],x=xyz[0]+off[0],y=xyz[1]+off[1],z=xyz[2]+off[2]))
 points=pd.DataFrame(probes);points.insert(0,'point_id',range(len(points)));points.to_csv(OUT/(house+'_PROBES.csv'),index=False);points[['point_id','x','y','z']].to_csv(LOCAL/(house+'_points.csv'),index=False)
 scp(LOCAL/(house+'_points.csv'),HOST+':'+REM+'/'+house+'_points.csv');scp(HOST+':/mnt/hgfs/workspace/GADEN_files/scenarios/'+house+'/OccupancyGrid3D.csv',str(OUT/(house+'_OccupancyGrid3D.csv')))
 assert sha(OUT/(house+'_OccupancyGrid3D.csv'))==next(r['occupancy_sha256'] for r in runs if r['house']==house)
 for ci in [i for i in range(8) if any(r['config_index']==i and r['house']==house for r in runs)]:
  rr=next(r for r in runs if r['config_index']==ci);context=rr['context'];folder=Path(rr['folder'])
  with tarfile.open(LOCAL/'wind_stage.tar.gz','w:gz') as tar:
   for p in sorted((folder/'wind').glob('wind_iteration_*')):tar.add(p,arcname=context+'/wind/'+p.name)
  scp(LOCAL/'wind_stage.tar.gz',HOST+':'+REM+'/wind_stage.tar.gz');ssh('tar -xzf '+REM+'/wind_stage.tar.gz -C '+REM)
  occ='/mnt/hgfs/workspace/GADEN_files/scenarios/'+house+'/OccupancyGrid3D.csv'
  cached=OUT/(context+'_WIND.csv')
  complete=cached.exists() and len(pd.read_csv(cached))==11*len(points)
  if not complete:
   ssh(ENV+REM+'/wind_query '+occ+' '+REM+'/'+context+'/wind '+REM+'/'+house+'_points.csv '+REM+'/'+context+'_WIND.csv')
   scp(HOST+':'+REM+'/'+context+'_WIND.csv',str(cached))
  assert len(pd.read_csv(cached))==11*len(points)
  print('wind probed '+context,flush=True)

# Replay only missing slow-context gas observations; existing fast outputs revalidated below.
for rr in runs:
 rid=rr['run_id'];target=OUT/(rid+'.observations.csv');existing=T0/(rid+'.observations.csv')
 if existing.exists():shutil.copyfile(existing,target)
 elif not target.exists():
  folder=Path(rr['folder'])
  with tarfile.open(LOCAL/'gas_stage.tar.gz','w:gz') as tar:
   for idx in sorted(set(rr['record_indices'])):tar.add(folder/f'iteration_{idx}',arcname=rid+f'/iteration_{idx}')
  scp(LOCAL/'gas_stage.tar.gz',HOST+':'+REM+'/gas_stage.tar.gz');ssh('tar -xzf '+REM+'/gas_stage.tar.gz -C '+REM+' && ln -sfn '+REM+'/'+rr['context']+'/wind '+REM+'/'+rid+'/wind')
  scp(OUT/(rid+'.route.csv'),HOST+':'+REM+'/route.csv')
  occ='/mnt/hgfs/workspace/GADEN_files/scenarios/'+rr['house']+'/OccupancyGrid3D.csv'
  ssh(ENV+'/home/zyc/task_sufficiency_t0_20261003/query '+occ+' '+REM+'/'+rid+' '+REM+'/route.csv '+REM+'/observations.csv')
  scp(HOST+':'+REM+'/observations.csv',str(target))
  cleanup="import pathlib,shutil;root=pathlib.Path('"+REM+"').resolve();p=(root/'"+rid+"').resolve();assert p.parent==root and p.name.startswith('ocb_r2_');shutil.rmtree(p)"
  ssh('python3 -c '+shlex.quote(cleanup))
 obs=pd.read_csv(target);route=pd.read_csv(OUT/(rid+'.route.csv'));assert len(obs)==301 and np.isfinite(obs.values).all() and np.all(obs.concentration>=0)
 assert np.array_equal(obs.record_index,route.record_index) and np.allclose(obs[['x','y','z']],route[['x','y','z']],atol=1e-6)
 inputs.append({'run_id':rid,'path':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'role':'queried_observations'})
 print('gas replay verified '+rid,flush=True)
pd.DataFrame(inputs).to_csv(OUT/'INPUT_SHA256.csv',index=False)
print('PREPARE COMPLETE:64 independent realizations; no new simulation',flush=True)
