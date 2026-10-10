from common import *
import subprocess,difflib
repo='D:/ZYC/A-gas/_reference_native_pmfs_upstream_20260923';pin='4e141e162551e674f2f30ddb8859136c72139aac'
names=subprocess.check_output(['git','-C',repo,'ls-tree','-r','--name-only',pin,'Environment_config/PMFS/navigation_config']).decode().splitlines()
files={}
for n in names:
 if '/resources/default_coppelia_scene.ttt' in n:continue
 rel=n.split('Environment_config/PMFS/',1)[1]
 files['official_E3/'+rel]=subprocess.check_output(['git','-C',repo,'show',pin+':'+n])
launch=(ROOT/'outputs/PMFS_PHYSICAL_CLOCK_NATIVE_LOCALIZATION_R7_20261009/N1_physical_clock_launch.py').read_text()
launch=launch.replace('/home/zyc/pmfs_physical_clock_localization_r7_20261009/runtime/',T+'/runtime/').replace('/r7/wind_to','/e3/wind_to')
launch=launch.replace(C+'/one_realization_C1',T+'/one_realization_E3').replace(C+'/derived_C1/OccupancyGrid3D.csv',T+'/derived_E3/OccupancyGrid3D.csv').replace(C+'/PHYSICAL_FRAME_TIME.csv',T+'/PHYSICAL_FRAME_TIME.csv').replace('"initial_iteration": 500','"initial_iteration": 200')
key='name="gaden_player",\n        parameters='
assert key in launch
launch=launch.replace(key,'name="gaden_player",\n        remappings=[("/odor_value","/e3/raw_odor_value"),("/wind_value","/e3/raw_wind_value")],\n        parameters=')
files['N1_E3_launch.py']=launch.encode()
driver=(ROOT/'outputs/PMFS_PHYSICAL_CLOCK_NATIVE_LOCALIZATION_R7_20261009/runtime_driver.py').read_text()
driver=driver.replace('/home/zyc/pmfs_physical_clock_localization_r7_20261009',T).replace('N1_physical_clock_launch.py','N1_E3_launch.py').replace("'scenario:=C','simulation:=C1'","'scenario:=E','simulation:=E3'").replace('/r7/wind_to','/e3/wind_to').replace('r7_capture_and_wind_adapter','e3_capture_and_wind_adapter').replace('C1_physics_qualification','E3_physics_qualification').replace('FRESH_C1_PINNED_PUBLIC_VERSION_WITH_PHYSICAL_CLOCK_ENGINEERING_ALIGNMENT','ONE_E3_OFFICIAL_PARAMETERS_N1_ENGINEERING_ALIGNMENT').replace("abs(pos.z-.4)","abs(pos.z-.5)")
driver=driver.replace(" # All raw sensors and TF retained; pose and map CDR retained at reduced rate.\n keep=('wind' in topic or '/PID/' in topic or topic in ['/tf','/tf_static','/clock'] or counts[topic]%10==1)"," # Full raw messages retained; no reduction.\n keep=True")
driver=driver.replace('from rclpy.node import Node','from rclpy.node import Node\nfrom rclpy.callback_groups import ReentrantCallbackGroup')
key="gas=node.create_client(GasPosition,'/odor_value');air=node.create_client(WindPosition,'/wind_value');action="
proxy='''service_group=ReentrantCallbackGroup()
raw_gas=node.create_client(GasPosition,'/e3/raw_odor_value',callback_group=service_group)
raw_wind=node.create_client(WindPosition,'/e3/raw_wind_value',callback_group=service_group)
service_log=(R/'service_queries.jsonl').open('w')
service_serial=0
async def forward_query(kind,client,request,response):
 global service_serial
 serial=service_serial;service_serial+=1
 before=node.get_clock().now().nanoseconds
 request_hex=serialize_message(request).hex()
 result=await client.call_async(request)
 service_log.write(json.dumps(dict(serial=serial,kind=kind,request_ns=before,response_ns=node.get_clock().now().nanoseconds,x=list(request.x),y=list(request.y),z=list(request.z),request_cdr_hex=request_hex,response_cdr_hex=serialize_message(result).hex()))+'\\n');service_log.flush()
 return result
async def gas_proxy(req,resp):return await forward_query('GasPosition',raw_gas,req,resp)
async def wind_proxy(req,resp):return await forward_query('WindPosition',raw_wind,req,resp)
gas_server=node.create_service(GasPosition,'/odor_value',gas_proxy,callback_group=service_group)
wind_server=node.create_service(WindPosition,'/wind_value',wind_proxy,callback_group=service_group)
gas=node.create_client(GasPosition,'/odor_value',callback_group=service_group);air=node.create_client(WindPosition,'/wind_value',callback_group=service_group);action='''
assert key in driver;driver=driver.replace(key,proxy)
key=" (R/'PREFLIGHT.json').write_text(json.dumps(pre,indent=2));status['preflight']='PASS';save_status()"
extra=''' # Before the single goal, verify native raw message types, frames, stamps and stationary TF.
 pid=latest['/PioneerP3DX/PID/Sensor_reading'];an=latest['/PioneerP3DX/Anemometer/WindSensor_reading']
 assert pid.raw_units==pid.UNITS_PPM and pid.technology==pid.TECH_PID and math.isfinite(pid.raw) and pid.raw>=0
 ages={}
 for label,msg in [('PID',pid),('anemometer',an)]:
  stamp=msg.header.stamp.sec*1000000000+msg.header.stamp.nanosec
  age=(node.get_clock().now().nanoseconds-stamp)/1e9
  assert stamp>0 and 0<=age<2,(label,age)
  ages[label]=age
 assert pid.header.frame_id=='PioneerP3DX_pid_frame' and an.header.frame_id=='PioneerP3DX_anemometer_frame'
 assert abs(pos.x+3)<1e-3 and abs(pos.y-4.5)<1e-3
 # Read the physically bound source neighborhood only as qualification; not fed to PMFS.
 probe=GasPosition.Request();probe.x=[-4.];probe.y=[-1.9];probe.z=[.7];pconc=call(gas,probe)
 assert all(math.isfinite(v) and v>=0 for v in pconc.positions[0].concentration)
 assert sum(pconc.positions[0].concentration)>0,'No valid generated gas response at release neighborhood'
 for n in ['gaden_player','PioneerP3DX/PID','PioneerP3DX/Anemometer','basic_sim']:
  with (R/('preflight_'+n.replace('/','_')+'_parameters.yaml')).open('w') as f:
   subprocess.run(['ros2','param','dump','/'+n],stdout=f,stderr=f,timeout=8)
 pre.update(message_age_sim_seconds=ages,PID_units='ppm',PID_model=30,PID_response='sum ppm; correction_factors=false from pinned code/default; resolved dump saved',probe_source_neighborhood_ppm=list(pconc.positions[0].concentration),probe_is_input_to_algorithm=False,gas_frame_binding='physical_clock_trace.csv',sensor_frames=[pid.header.frame_id,an.header.frame_id],native_goal_count=0)
 (R/'PREFLIGHT.json').write_text(json.dumps(pre,indent=2));status['preflight']='PASS';save_status()'''
assert key in driver;driver=driver.replace(key,extra)
driver=driver.replace('wire.close();','wire.close();service_log.close();')
files['runtime_driver.py']=driver.encode()
for n in ['N1_E3_launch.py','runtime_driver.py']:
 compile(files[n].decode(),n,'exec');(OUT/n).write_bytes(files[n])
(OUT/'LAUNCH_ENGINEERING_DIFF.patch').write_text(''.join(difflib.unified_diff((OUT/'official/launch/main_simbot_launch.py').read_text().splitlines(True),launch.splitlines(True),fromfile='official/main_simbot_launch.py',tofile='N1_E3_launch.py')),encoding='utf-8')
code=r'''
import shutil,hashlib
assert json.loads((t/'GATE2.json').read_text())['verdict'].startswith('PASS')
assert not (t/'RUN_STARTED.json').exists()
prefix=t/'overlay';share=prefix/'share/pmfs_env';shutil.copytree(t/'official_E3',share)
marker=prefix/'share/ament_index/resource_index/packages/pmfs_env';marker.parent.mkdir(parents=True);marker.write_text('')
(t/'runtime').mkdir()
assets={str(p.relative_to(t/'official_E3')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (t/'official_E3').rglob('*') if p.is_file()}
(t/'OFFICIAL_RUNTIME_ASSETS.json').write_text(json.dumps(assets,indent=2))
print(json.dumps(dict(runtime_prepared=True,overlay=str(prefix),parameters=dict(initialExplorationMoves=2,stepsSourceUpdate=3,sourceDiscriminationPower=.3,maxSearchTime=300.,convergence_thr=1.5,player_initial_iteration=200,sensor_z=.5),native_goal_count=0,service_proxy='transparent async CDR capture; no values modified')))
'''
print(put(files,code,'PREPARE_RUNTIME',45))
