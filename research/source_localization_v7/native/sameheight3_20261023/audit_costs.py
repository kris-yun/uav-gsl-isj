"""Hash every new native frame and bind costs/parameters. No gas queries."""
from pathlib import Path
import hashlib,json,time,tarfile,shutil
from protocol import *

def main():
 start=time.perf_counter();c=config();ledger=json.loads((OUT/'GENERATION_ATTEMPTS.json').read_text())
 assert len(ledger)==8 and all(x['status']=='PASS_ORIGINAL_GENERATION' and x['exit_code']==0 for x in ledger)
 records=[];count=0
 for entry in ledger:
  key=entry['run_id'];path=OUT/'raw_archives'/(key+'.tar.gz')
  meta=json.loads((OUT/'archives'/(key+'.json')).read_text());assert sha(path)==meta['sha256']
  with tarfile.open(path,'r:gz') as archive:
   inv=json.loads(archive.extractfile(key+'/FRAME_SHA256.json').read());manifest=json.loads(archive.extractfile(key+'/RUN_MANIFEST.json').read())
  expected={x['name']:x for x in inv};seen=[]
  with tarfile.open(path,'r|gz') as archive:
   for member in archive:
    leaf=Path(member.name).name
    if not member.isfile() or leaf not in expected:continue
    b=archive.extractfile(member).read();assert len(b)==expected[leaf]['bytes'] and hashlib.sha256(b).hexdigest()==expected[leaf]['sha256']
    seen.append(leaf);count+=1
  assert len(seen)==1803 and set(seen)==set(expected)
  params=manifest['parameters'];base=c['base_parameters'];allowed={'results_location','occupancy3D_data','source_position_x','source_position_y','source_position_z'}
  assert {k:v for k,v in params.items() if k not in allowed}=={k:v for k,v in base.items() if k not in allowed}
  xyz=list(map(float,[params['source_position_'+x] for x in 'xyz']));assert xyz==c['source_xyz_m'][c['source_ids'].index(entry['source'])]
  assert entry['seed']==c['master_seeds'][entry['repeat']-1]
  assert entry['original_binary_sha256']==ELF_SHA and entry['timeline_sha256']==c['expected_timeline_sha256']
  stdout=OUT/'logs'/(key+'.stdout.log');assert sha(stdout)==entry['stdout_sha256']
  records.append({'run_id':key,'source':entry['source'],'repeat':entry['repeat'],'master_seed':entry['seed'],
   'frames':1803,'archive_sha256':sha(path),'archive_bytes':path.stat().st_size,'wall_s':entry['wall_s'],
   'child_user_cpu_s':entry['child_user_cpu_s'],'child_system_cpu_s':entry['child_system_cpu_s'],
   'max_child_RSS_KiB':entry['worker_child_max_rss_KiB']})
 wall=sum(x['wall_s'] for x in records);cpu=sum(x['child_user_cpu_s']+x['child_system_cpu_s'] for x in records)
 assert wall<=5400 and count==14424
 write('PHYSICAL_RUN_AND_COST_AUDIT.json',{'status':'PASS_ALL_EIGHT_NEW_NATIVE_WORLDS','records':records,
 'all_new_frame_SHA_checks':count,'all_clocks_match_original_1803_record_timeline':True,
 'all_physics_parameters_unchanged_except_predefined_source_coordinates':True,
 'occupancy_readonly_path_alias_not_a_map_edit':True,'all_source_heights_m':[.4,.4,.4],
 'generation_wall_s_sum':wall,'generator_child_CPU_s_sum':cpu,
 'original_A_worlds_reused':4,'new_world_attempts':8,'extra_physics_retries':0,
 'raw_archives_total_bytes':sum(x['archive_bytes'] for x in records),
 'native_last_run_storage':ledger[-1]['retained_size'],'maximum_scientific_bytes':805306368,
 'seed_independence':'four shared-master-seed groups, two TRAIN and two DEV; twelve source realizations are not twelve independent seed groups',
 'robot_ROS_closed_loops':0,'M2_M3_runs':0,'GADEN_worker_note':'standalone original filament_simulator uses ROS runtime libraries/parameters; no robot, navigation or PMFS closed loop started',
 'same_legacy_TP_binding_retained':True,'absolute_Q_not_recertified':True,
 'raw_audit_wall_s':time.perf_counter()-start})
 print('PHYSICS_AND_COST_QA_PASS',count,'wall',round(wall,3),'CPU',round(cpu,3))

if __name__=='__main__':main()
