from common_n import *
import csv,numpy as np,shutil,os
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def copy(src,dest):
 dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');support=RAW/'support';support.mkdir(exist_ok=True)
assert len(list((D/'native_cold_results').glob('*/EXECUTION.json')))==18,'Wait for all eighteen registered native histories'
parent=BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
copy(parent/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv',support/'geometry/OccupancyGrid3D.csv');copy(parent/'frozen_B4_inputs/derived_B4/wind/wind_iteration_10',support/'geometry/wind_iteration_10')
copy(CORE/'native_inputs/inputs/DERIVED/input.csv',support/'geometry/native_grid.csv')
for n in ['Math_accessors.cpp','Simulations_native_with_state_access.cpp','PMFSLib_frozen.cpp']:copy(CORE/'source/native'/n,support/'source'/n)
for rel in ['source/sensor/fake_gas_sensor.cpp','source/gaden/include/gaden/datatypes/GasTypes.hpp']:copy(parent/'frozen_B4_inputs'/rel,support/'source'/Path(rel).name)
copy(BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/runtime/preflight_PioneerP3DX_PID_parameters.yaml',support/'source/actual_PID_parameters.yaml')
records=[]
for kind in ['readout','C_readout']:
 for folder in (D/kind).iterdir():
  if not folder.is_dir() or not (folder/'QUERY_OUTPUT.csv').exists():continue
  q=rows(folder/'QUERY_OUTPUT.csv');assert len(q)==22400
  val=np.array([[float(r[k]) for k in ['ppm_float32','physical_free','wind_x','wind_y','wind_z']] for r in q],dtype='<f4').reshape(50,448,5)
  frame=np.array([int(q[b*448]['frame']) for b in range(50)],dtype=np.int32);position=np.array([[float(r[k]) for k in ['x','y','z']] for r in q[:448]],dtype='<f4')
  dest=support/'readouts'/folder.name;dest.mkdir(parents=True,exist_ok=True)
  with np.load(folder/'READOUT_FIELDS.npz',allow_pickle=False) as z:
   np.savez_compressed(dest/'FIELDS.npz',queries=val,frames=frame,first_block_positions=position,O0=z['O0'],O1=z['O1'],O0_blurred=np.fromfile(folder/'native_blur/O0/blurred.f32',dtype='<f4'),O1_blurred=np.fromfile(folder/'native_blur/O1/blurred.f32',dtype='<f4'),A1=np.fromfile(folder/'A1.f32',dtype='<f4'))
  for n in ['EVENTS_O1.csv','SELECTED_FRAME_LINEAGE.csv']:copy(folder/n,dest/n)
  records.append(dict(id=folder.name,full_query_csv_path=folder.as_posix()+'/QUERY_OUTPUT.csv',full_query_csv_SHA256=sha(folder/'QUERY_OUTPUT.csv'),packed_numeric_SHA256=sha(dest/'FIELDS.npz'),all_query_values_packaged=True,queries=22400))
dump(support/'READOUT_PACKING_INDEX.json',records)
# Every posterior and every blurred candidate prediction from primary native histories.
for run in (D/'native_cold_results').iterdir():
 if not run.is_dir() or not (run/'EXECUTION.json').exists():continue
 dest=support/'native'/run.name
 for p in run.iterdir():
  if p.is_file() and p.name in ['EXECUTION.json','update_ledger.csv','final_map.csv','final_posterior.f64','event_cell_lineage.csv'] or p.is_file() and p.name.startswith('map_blocks_'):copy(p,dest/p.name)
 for u in run.glob('update_*'):
  if not u.is_dir():continue
  for p in u.iterdir():
   if p.is_file():copy(p,dest/u.name/p.name)
  for p in (u/'maps').glob('*.f32'):
   if '_unblurred' not in p.name:copy(p,dest/u.name/'maps'/p.name)
  # Release-point files are large. Package true/peak selections; preserve all others externally with hash index.
  for c in rows(u/'candidates.csv')[:1]:copy(u/c['points_file'],dest/u.name/c['points_file'])
 copy(CORE/'native_inputs/inputs/DERIVED/metadata.csv',dest/'metadata.csv')
# Original and corrected point-model evidence.
for c in ['C7','K2','B000','B001','B002']:
 for i in [0,1]:
  f=D/f'point_corrected_results/{c}_R{i}/forward';dest=support/'point'/f'{c}_R{i}'
  for p in f.rglob('*'):
   if p.is_file():copy(p,dest/p.relative_to(f))
for c in ['C7','K2','B000','B001','B002']:
 for group in ['R0','R1','R01']:copy(D/f'point_corrected_scores/{c}_{group}.f32',support/'point_scores'/f'{c}_{group}.f32')
for p in (D/'confirmation_reference_freeze').iterdir():copy(p,support/'confirmation_reference'/p.name)
# All new-bank metadata, accounting and three prechosen raw frames; full banks remain on shared disk.
gas=[]
for root,mode in [(D/'factorial','FACTORIAL'),(D/'fresh/realizations','FRESH_WORLD')]:
 for bank in root.iterdir():
  if not bank.is_dir() or not (bank/'QUALIFICATION.json').exists():continue
  dest=support/'banks'/bank.name
  for p in bank.iterdir():
   if p.is_file() and (p.suffix in ['.json','.yaml','.csv','.txt'] or p.name.startswith('RNG.')):copy(p,dest/p.name)
  allframes=rows(bank/'ALL_FRAME_SHA256_AND_TIME.csv');eligible=[r for r in allframes if float(r['physical_snapshot_time_s'])>=320];sel=[eligible[0],eligible[len(eligible)//2],eligible[-1]]
  for r in sel:copy(bank/'bank'/('iteration_'+r['frame']),dest/'selected_frames'/('iteration_'+r['frame']))
  gas.append(dict(id=bank.name,role=mode,full_bank=bank.as_posix(),raw_all_frame_count=len(allframes),selected_raw_frames=[r['frame'] for r in sel],full_raw_bank_packaged=False,full_all_frame_hash_time_index_packaged=True))
dump(support/'RAW_BANK_COVERAGE.json',gas)
for label in ['E3','B4']:
 a=next(r for r in load(CORE/'HISTORICAL_ANCHOR_PLAN.json') if r['label']==label);old=Path(a['expected_snapshot']);dest=support/'historical'/label
 for n in ['input.csv','metadata.json','posterior.f64','candidates.csv','gaussian_cache.f32']:copy(old/n,dest/n)
 for c in rows(old/'candidates.csv'):copy(old/c['map_file'],dest/c['map_file'])
 for suffix in ['saved_map_scores','short_forward_OFF']:
  for p in (D/'native_results'/(label+'_'+suffix)).rglob('*'):
   if p.is_file():copy(p,support/'historical_replays'/(label+'_'+suffix)/p.relative_to(D/'native_results'/(label+'_'+suffix)))
first=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/runtime/updates/update_0';c=rows(first/'candidates.csv')[0]
for n in ['candidates.csv','gaussian_initial.csv','gaussian_cache.f32',c['map_file'],c['points_file']]:copy(first/n,support/'cold_golden'/n)
copy(D/'cold_FIRST_OFF/forward/gaussian_initial.csv',support/'cold_anchor/gaussian_initial.csv')
for p in (D/'cold_FIRST_OFF/forward').rglob('*'):
 if p.is_file():copy(p,support/'cold_anchor'/p.relative_to(D/'cold_FIRST_OFF/forward'))
spot=rows(CORE/'RAW_PHYSICAL_CONTRIBUTION_SPOTCHECK.csv')
for r in spot:
 src=parent/f"native_reference_evidence/realizations/{r['candidate']}_{r['reference']}/bank/iteration_{r['frame']}"
 copy(src,support/'raw_spotchecks'/f"{r['candidate']}_{r['reference']}"/src.name)
copy(BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/independent_raw_query_verify/verify_raw_receiver_queries.py',CORE/'source/portable/raw_decode.py')
copy(BASE/'work/pmfs_rk2b_continuous_20261010/cache_native.py',CORE/'source/portable/receiver_math.py')
for run in (D/'native_cold_results').iterdir():
 if run.is_dir() and (run/'EXECUTION.json').exists():
  oid=run.name.removeprefix('FRESH_N0_').removeprefix('N0_')
  local=CORE/f'native_inputs/events/{oid}.csv'
  if not local.exists():
   p=subprocess.run(SSH+['cat '+REMOTE+'/events/'+oid+'.csv'],capture_output=True,timeout=15);assert p.returncode==0
   local.parent.mkdir(parents=True,exist_ok=True);local.write_bytes(p.stdout)
dump(CORE/'PACKAGED_SUPPORT_COVERAGE.json',dict(readout_banks=len(records),query_values=22400*len(records),new_banks=len(gas),complete_primary_native_histories=sum((p/'EXECUTION.json').exists() for p in (D/'native_cold_results').iterdir() if p.is_dir()),
 source_release_points='Only first candidate per update packaged; all release points preserved in full external primary history with hashes',raw_generation='Three preselected raw frames per new bank plus complete frame/time/hash indices; full raw banks preserved externally',old_banks='Not re-packed; native query values are fully included; provenance/locations remain explicit'))
print(json.dumps({'status':'PORTABLE_SUPPORT_BUILT','readout_banks':len(records),'new_banks':len(gas),'raw_bytes':sum(p.stat().st_size for p in RAW.rglob('*') if p.is_file())}))
