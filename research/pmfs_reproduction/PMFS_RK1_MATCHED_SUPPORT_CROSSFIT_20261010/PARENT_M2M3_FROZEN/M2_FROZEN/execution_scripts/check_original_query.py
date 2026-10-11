from common import *
import csv,io,hashlib,shutil
schedule=W/'scoring_contract/FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv'
with schedule.open(encoding='utf-8',newline='') as f:records=list(csv.DictReader(f))
buffer=io.StringIO(newline='');writer=csv.DictWriter(buffer,fieldnames=['query_id','frame','x','y','z']);writer.writeheader()
for row in sorted(records,key=lambda r:int(r['physical_frame'])):
    writer.writerow(dict(query_id=f"block{row['block_id']}_branch{row['membership_branch']}",frame=row['physical_frame'],
                         x=row['sensor_x'],y=row['sensor_y'],z=row['sensor_z']))
files={'ORIGINAL_NATIVE_RECEPTOR_QUERIES.csv':buffer.getvalue().encode()}
code=r'''
import os,subprocess,time,csv,hashlib
c=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws')
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(c/'install/gaden_common/lib')+':'+str(c/'build/gaden_common/third_party/gaden_core/third_party/libbsc')+':/opt/ros/humble/lib'
env['OMP_NUM_THREADS']='1'
start=time.monotonic();command=[str(t/'query_native'),'/home/zyc/pmfs_b4_native_validation_20261009/derived_B4',
 '/home/zyc/pmfs_b4_native_validation_20261009/one_realization_B4',str(t/'ORIGINAL_NATIVE_RECEPTOR_QUERIES.csv'),str(t/'ORIGINAL_NATIVE_QUERY.csv')]
r=subprocess.run(command,env=env,capture_output=True,text=True,timeout=60)
(t/'original_query.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
print(json.dumps(dict(wall_s=time.monotonic()-start,output=(t/'ORIGINAL_NATIVE_QUERY.csv').read_text(),exit_code=r.returncode)))
'''
result=json.loads(upload(files,code,'ORIGINAL_NATIVE_QUERY_ANCHOR',75))
prediction=list(csv.DictReader(io.StringIO(result.pop('output'))));observed={f"block{r['block_id']}_branch{r['membership_branch']}":r for r in records}
errors=[abs(float(r['ppm_float32'])-float(observed[r['query_id']]['observed_pid_ppm'])) for r in prediction]
result.update(queries=len(prediction),maximum_abs_ppm_difference=max(errors),verdict='PASS_NATIVE_PHYSICAL_QUERY_TO_ORIGINAL_PID' if max(errors)<=1e-7 else 'HOLD_ORIGINAL_QUERY_MISMATCH',
              scheduler_sha256=hashlib.sha256(schedule.read_bytes()).hexdigest())
with (OUT/'ORIGINAL_NATIVE_QUERY.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(prediction[0]));writer.writeheader();writer.writerows(prediction)
(OUT/'ORIGINAL_QUERY_ANCHOR.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
shutil.copytree(W/'scoring_contract',OUT/'observation_lineage')
supplement=dict(purpose='Pre-query exact consumer membership and deliberately unmatched-map definition',
 receptor_schedule_sha256=hashlib.sha256(schedule.read_bytes()).hexdigest(),ambiguous_block_id=40,
 ambiguity_rule='Both membership branches fixed and reported; do not count both as observations; if rankings disagree, HOLD',
 actual_sensor_height=-.20000000298023224,actual_block_members=1,physical_time_anchor='Actual gas service frame-query trace, not block endpoint',
 unmatched_physical_map_definition='At each branch-selected 50 actual receptor physical targets, concentration>0.1ppm at each free cell centre and sensor height; average over times. Not IID observations.',
 aligned_map_definition='Native PMFSLib update with each source-bank PID block event and original frozen wind/xy covariates; map descriptive squared discrepancy only',
 aligned_reference_ranking='No joint map likelihood; primary heldout qualification uses the frozen raw-event log+Brier scores')
(OUT/'PRE_QUERY_OBSERVATION_CONTRACT.json').write_text(json.dumps(supplement,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2));assert result['verdict'].startswith('PASS')
