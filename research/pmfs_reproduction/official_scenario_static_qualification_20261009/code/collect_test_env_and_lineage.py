from pathlib import Path
import json,subprocess,hashlib,shutil,os
import yaml

root=Path(__file__).resolve().parents[2]
out=root/'outputs/PMFS_OFFICIAL_SCENARIO_STATIC_QUALIFICATION_20261009'
gaden=root/'work/pmfs_r5/GADEN'
pin='ccb02e959a45a188e4b6c78792e197633fc64f1c'
assert subprocess.check_output(['git','-C',str(gaden),'rev-parse','HEAD']).decode().strip()==pin
tree={}
for line in subprocess.check_output(['git','-C',str(gaden),'ls-tree','-r',pin,'--','test_env']).decode().splitlines():
    meta,n=line.split('\t',1);tree[n]=meta.split()[2]
assets=[];rows=[]
for scenario in sorted((gaden/'test_env/scenarios').iterdir()):
    if not scenario.is_dir():continue
    config=scenario/'environment_configurations/config1/config.yaml'
    sim=scenario/'environment_configurations/config1/simulations/sim1/sim.yaml'
    scene=scenario/'environment_configurations/config1/scenes/scene1.yaml'
    for f in scenario.rglob('*'):
        if not f.is_file() or f.suffix not in ['.yaml','.stl','.gproj']:continue
        rel=f.relative_to(gaden).as_posix()
        raw=subprocess.check_output(['git','-C',str(gaden),'show',pin+':'+rel])
        assets.append(dict(provider='GADEN_FIXED_GIT_OBJECT',revision=pin,repository=str(gaden),path=rel,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        if f.suffix in ['.yaml','.gproj']:
            p=out/'evidence/official_gaden'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    c=yaml.safe_load(config.read_text());s=yaml.safe_load(sim.read_text());playback=yaml.safe_load(scene.read_text())
    wp=(config.parent/c['unprocessed_wind_files']).resolve()
    # Directory/name is not a time-varying classification: numeric evidence is linked later.
    rows.append(dict(id='GADEN_'+scenario.name,family='GADEN_TEST_ENV',scenario=scenario.name,configuration='config1',simulation_id='sim1',
        config_path=config.relative_to(gaden).as_posix(),sim_path=sim.relative_to(gaden).as_posix(),scene_path=scene.relative_to(gaden).as_posix(),
        config=c,simulation=s,scene=playback,wind_prefix=str(wp),source_xyz=s['source']['position'],source_type=s['source']['sourceType'],
        source_line_end=s['source'].get('lineEnd'),processed_3d_exists=(config.parent/'OccupancyGrid3D.csv').exists(),
        official_PMFS_map_binding=False,gas_frames_in_pinned_test_env=0,raw_ROS_events_attached=False))
for n in ['test_env/ros_params/gaden_params.yaml','test_env/launch/main_simbot_launch.py','test_env/launch/gaden_player_launch.py']:
    raw=subprocess.check_output(['git','-C',str(gaden),'show',pin+':'+n]);p=out/'evidence/official_gaden'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    assets.append(dict(provider='GADEN_FIXED_GIT_OBJECT',revision=pin,repository=str(gaden),path=n,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
wind_objects=[]
for r in json.loads((out/'RAW_ASSET_HASHES.json').read_text()):
    if r['provider']!='LOCAL_PINNED_GADEN_COPY':continue
    f=Path(r['path']);relative=f.relative_to(gaden).as_posix();b=f.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    tracked=tree.get(relative)
    original=subprocess.check_output(['git','-C',str(gaden),'show',pin+':'+relative])
    text_equal=b.replace(b'\r\n',b'\n')==original.replace(b'\r\n',b'\n')
    wind_objects.append(dict(path=str(f),revision=pin,git_path=relative,git_blob=tracked,raw_blob=blob,
        raw_blob_equals_official=tracked==blob,sha256=hashlib.sha256(b).hexdigest(),official_sha256=hashlib.sha256(original).hexdigest(),
        normalized_text_equals_official=text_equal))
    assert text_equal,(relative,'numeric text differs from pinned source')

official_working=Path('D:/ZYC/A-gas/workspace/GasSourceLocalization-humble/Environment_config/PMFS/scenarios')
local_inventory=[]
for scenario in 'ABCDE':
    p=official_working/scenario;gas=p/'gas_simulations'
    frames=[]
    if gas.exists():
        for d,sub,files in os.walk(gas):
            if len(Path(d).relative_to(gas).parts)>=3:sub[:]=[]
            f=[n for n in files if n.startswith('iteration_') and n[10:].isdigit()]
            if f:frames.append(dict(path=d,count=len(f)))
    local_inventory.append(dict(scenario=scenario,path=str(p),exists=p.exists(),occupancy3d_exists=(p/'OccupancyGrid3D.csv').exists(),gas_recordings=frames))

# Freeze the exact source evidence already used for the geometry/time contracts.
src=root/'outputs/PMFS_R6_CAUSE_TRIAGE_20261009/inputs'
for name in ['Grid2D.hpp','PMFSLib.cpp','PMFS.cpp','Algorithm.cpp','StopAndMeasureState.cpp','Occupancy.hpp']:
    f=src/'official_source'/name;p=out/'evidence/consumer_source'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,p)
    assets.append(dict(provider='PREVIOUS_FIXED_UPSTREAM_SOURCE',path=str(f),revision='4e141e162551e674f2f30ddb8859136c72139aac',bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
for name in ['WindSequence.cpp','RunningSimulation.cpp','PlaybackSimulation.cpp']:
    f=src/'gaden_core_existing/src'/name;p=out/'evidence/legacy_compatible_reader_source'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,p)
    assets.append(dict(provider='PREVIOUS_LEGACY_COMPATIBLE_GADEN_DEPENDENCY',path=str(f),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),note='Reader semantics only; not the new-clean-generation core revision.'))
for n in ['PRE_GENERATION_QUALIFICATION.json','CLEAN_C1_QUALIFICATION.json','GENERATION_RESULT.json','PRISTINE_CORE_DEPENDENCY_LOCK.json']:
    f=root/'outputs/PMFS_R6_CAUSE_TRIAGE_20261009/clean_C1'/n
    if f.exists():p=out/'evidence/frozen_C1'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,p)
(out/'OFFICIAL_GADEN_CONFIG_RAW.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
(out/'GADEN_FIXED_GIT_WIND_CHECK.json').write_text(json.dumps(wind_objects,indent=2),encoding='utf-8')
(out/'LOCAL_PMFS_WORKING_ASSET_PRESENCE.json').write_text(json.dumps(local_inventory,indent=2),encoding='utf-8')
(out/'TEST_ENV_AND_SOURCE_HASHES.json').write_text(json.dumps(assets,indent=2),encoding='utf-8')
print(json.dumps(dict(GADEN_test_env_scenarios=len(rows),wind_files_numeric_text_equal_pinned_git=len(wind_objects),
    wind_files_byte_equal_pinned_git=sum(r['raw_blob_equals_official'] for r in wind_objects),
    existing_PMFS_official_working_gas_recordings=sum(len(r['gas_recordings']) for r in local_inventory))))
