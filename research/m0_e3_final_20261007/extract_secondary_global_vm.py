"""Complete R0 secondary columns from saved snapshots; no gas simulation."""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007/e3_final')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
assert read(R/'E3_PROGRESS.json')['qualified_completed']==28
assert not (R/'secondary_global').exists();R.joinpath('secondary_global').mkdir()
old=read(R/'PARENT_E1_HELPER_BUILD.json')['argv'];args=[str(R/'native_global_column.cpp') if s.endswith('/native_e1_audit.cpp') else (str(R/'bin/native_global_column') if s.endswith('/bin/native_e1_audit') else s) for s in old]
with (R/'global_helper_build.log').open('wb') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
M=read(R/'E3_ASSET_MANIFEST.json');H=read(R/'E3_HISTORY_INDEX.json');new=read(R/'E3_COMPLETED_RUNS.json');A=read(R/'E3_AUTHORIZATION.json');reports=[];start=time.monotonic()
for row in A['all_frozen_rows']:
    rid=row['run_id'];h=next((v for v in H if v['frozen_row']['run_id']==rid),None);manifest=h['manifest'] if h else next(v for v in new if v['run_id']==rid);out=R/'secondary_global'/rid;out.mkdir()
    argv=[str(R/'bin/native_global_column'),'e1',str(R/'projects'/row['wind_arm']),manifest['native_raw_path'],str(out),str(R/'M0_UAV_ROUTE_POINTS.csv')];t=time.monotonic()
    with (out/'extract.stdout.log').open('wb') as f:subprocess.run(['/usr/bin/time','-v','-o',str(out/'extract.time.txt'),*argv],stdout=f,stderr=subprocess.STDOUT,check=True)
    assert sha(out/'route.csv')==sha(Path(manifest['native_audit_path'])/'route.csv')
    # Redundant position/clock dumps are identical to original native extraction.
    for filename in ['filament_states.f32','native_frames.csv']:assert sha(out/filename)==sha(Path(manifest['native_audit_path'])/filename)
    duplicates=R/'audit/_secondary_duplicate_readbacks'/rid;duplicates.mkdir(parents=True)
    for filename in ['filament_states.f32','native_frames.csv','route.csv']:(out/filename).rename(duplicates/filename)
    reports.append({'run_id':rid,'argv':argv,'wall_s':time.monotonic()-t,'secondary_only':True,'original_route_and_state_bit_identity':True,'native_column_grid':[120,80],'native_samples_per_column_z':47,'simulation_runs_added':0})
    print(json.dumps({'secondary_completed':len(reports),'run_id':rid}),flush=True)
(R/'SECONDARY_GLOBAL_EXTRACTION.json').write_text(json.dumps({'reports':reports,'wall_all40_s':time.monotonic()-start,'source_sha256':sha(R/'native_global_column.cpp'),'helper_binary_sha256':sha(R/'bin/native_global_column'),'build_argv':args,'primary_metric_uses_ROI_columns_only':True,'new_scientific_runs':0},indent=2)+'\n')
