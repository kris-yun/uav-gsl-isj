"""Finite matched-kernel intervention ladder. Preserve every first outcome."""
from pathlib import Path
import csv,hashlib,json,os,resource,shutil,subprocess,time,zlib,struct
import numpy as np

B=Path('/mnt/hgfs/workspace/METHOD_COMPARISON_O24_1M2_20261024');P=B/'outputs/E3_CAUSAL_PAIR_20261025';O=B/'outputs/E3_TRANSPORT_CAUSE_20261025';W=B/'outputs/E3_HORIZONTAL_WIND_ORACLE_20261025';CORE=P/'build_source/gaden_core';C=B/'method_source/E3_TRANSPORT_CAUSE_20261025';G=Path('/home/zyc/ros2_ws/research_runs/e3_transport_cause_20261025')
def load(p):return json.loads(p.read_text())
def put(p,x):p.write_text(json.dumps(x,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n')
def rows(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare_core():
    patch=O/'core_patch';patch.mkdir(exist_ok=True);header=G/'override/gaden/internal/MathUtils.hpp';header.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(P/'provenance/MathUtils.instrumented.hpp',header);shutil.copy2(header,patch/'MathUtils.instrumented.hpp')
    env=(CORE/'src/Environment.cpp').read_text();needle='return (coords - description.minCoord) / description.cellSize;';assert env.count(needle)==1;env=env.replace(needle,'if(const char* strict=std::getenv("E3_CAUSE_STRICT_BOUNDS");strict && std::string(strict)=="1")return Vector3i(glm::floor((coords-description.minCoord)/description.cellSize));\n        '+needle);(patch/'Environment.cpp').write_text(env)
    source=(CORE/'src/RunningSimulation.cpp').read_text();needle='gaden::Vector3 windVec = SampleWind(cellIdx);';assert source.count(needle)==1;source=source.replace(needle,needle+'\n            static const std::string causal_mode=std::getenv("E3_CAUSE_MODE")?std::getenv("E3_CAUSE_MODE"):"full3d";\n            if(causal_mode=="no_vwind")windVec.z=0;')
    needle='newPosition.z += terminal_buoyancy_velocity * parameters.deltaTime;';assert source.count(needle)==1;source=source.replace(needle,'if(causal_mode!="no_buoyancy")'+needle)
    needle='newPosition.z += gaussian.nextValue(0, parameters.filamentNoise_std) * parameters.deltaTime;';assert source.count(needle)==1;source=source.replace(needle,needle+'\n            if(causal_mode.rfind("plane",0)==0)newPosition.z=simulationMetadata.source->sourcePosition.z;')
    (patch/'RunningSimulation.cpp').write_text(source);shutil.copy2(CORE/'src/YAML_Conversions.hpp',patch/'YAML_Conversions.hpp')
    put(O/'CORE_PATCH_IDENTITY.json',dict(original_running_source_sha256=sha(CORE/'src/RunningSimulation.cpp'),original_environment_source_sha256=sha(CORE/'src/Environment.cpp'),running_patch_sha256=sha(patch/'RunningSimulation.cpp'),environment_patch_sha256=sha(patch/'Environment.cpp'),default_original_body_preserved=True,interventions=['coords floor only under explicit strict flag','vertical displacement constraint after consuming all3noise draws','optional zero_vz or zero_buoyancy','optional coarsewind subclass ornoise0.05input'],frozen_O24_touched=False))

def main():
    assert not (O/'EXECUTION_RECEIPT.json').exists();G.mkdir(parents=True,exist_ok=True);(O/'logs').mkdir(exist_ok=True);(O/'runs').mkdir(exist_ok=True);prepare_core();plan=load(O/'PREREGISTERED_CAUSAL_CONTRACT.json');cost=load(O/'COST.json') if (O/'COST.json').exists() else [];start=time.monotonic()-sum(c['wall_s'] for c in cost)
    def limits():resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_FSIZE,(16777216,16777216))
    def execute(name,args,envextra=None):
        original_name=name;attempt=1
        while (O/'logs'/(name+'.stdout')).exists():attempt+=1;name=original_name+'_attempt'+str(attempt)
        t=time.monotonic();a=resource.getrusage(resource.RUSAGE_CHILDREN);env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1');env.update(envextra or {})
        with (O/'logs'/(name+'.stdout')).open('w') as so,(O/'logs'/(name+'.stderr')).open('w') as se:
            p=subprocess.Popen(list(map(str,args)),stdout=so,stderr=se,env=env,preexec_fn=limits)
            while p.poll() is None:
                if time.monotonic()-start>900 or time.monotonic()-t>120:p.kill();p.wait();raise RuntimeError('WALL_CAP')
                if sum(f.stat().st_size for f in O.rglob('*') if f.is_file())>134217728:p.kill();p.wait();raise RuntimeError('OUTPUT_CAP')
                time.sleep(.2)
        b=resource.getrusage(resource.RUSAGE_CHILDREN);cost.append(dict(stage=name,argv=list(map(str,args)),returncode=p.returncode,wall_s=time.monotonic()-t,CPU_s=b.ru_utime+b.ru_stime-a.ru_utime-a.ru_stime));put(O/'COST.json',cost);assert p.returncode==0,(name,p.returncode)
    try:
        include=['-I'+str(G/'override'),'-I'+str(CORE/'include'),'-I'+str(CORE/'third_party/DDA/include'),'-I'+str(CORE/'third_party/DDA/third_party/glm'),'-I'+str(CORE/'third_party/yaml-cpp/include'),'-I'+str(CORE/'third_party/libbsc')]
        args=['g++','-std=c++20','-O2','-DGADEN_ROS=0','-DGPU_ACCELERATION=0','-include','bits/stdc++.h','-ffunction-sections','-fdata-sections','-fopenmp']+include+[C/'driver.cpp']+[CORE/'src'/f for f in ['Simulation.cpp','PlaybackSimulation.cpp','WindSequence.cpp','GasSource.cpp']]+[O/'core_patch/RunningSimulation.cpp',O/'core_patch/Environment.cpp','-L'+str(P/'native_runtime'),'-Wl,-rpath,'+str(P/'native_runtime'),'-Wl,--gc-sections','-lfmt','-lyaml-cpp','-lz','-lbsc','-o',G/'cause_driver']
        if not (O/'ORIGINAL_KERNEL_PARITY.json').exists():execute('build_cause_driver',args)
        def run(name,task,words):
            directory=O/'runs'/name
            if directory.exists():
                assert load(directory/'TASK.json')==task and (directory/'RESULT.json').exists() and len(rows(directory/'RESPONSES.csv'))==604,'REFUSE_PARTIAL_OR_DIFFERENT_RERUN'
                assert any(c['stage']==name and c['returncode']==0 for c in cost),'MISSING_SUCCESSFUL_CALL_COST'
                if task['strict_bounds']:assert load(directory/'RESULT.json')['outside_particle_time_samples']==0
                return directory
            directory.mkdir();put(directory/'TASK.json',task);env=dict(E3_CAUSE_MODE=task['mode'],E3_CAUSE_STRICT_BOUNDS='1' if task['strict_bounds'] else '0',E3_GAUSSIAN_WORDS=','.join(map(str,words['gaussian'])),E3_UNIFORM_WORDS=','.join(map(str,words['uniform'])),E3_RNG_TRACE=str(directory/'RNG'))
            execute(name,[G/'cause_driver',directory/'TASK.json',O/'inputs/OccupancyGrid3D.csv',O/'inputs/wind_iteration_0',O/'inputs/QUERIES.csv',directory],env)
            result=load(directory/'RESULT.json');assert result['queries']==604
            if task['strict_bounds']:assert result['outside_particle_time_samples']==0,'STRICT_BOUNDARY_STILL_HAS_OOB_CENTERS'
            return directory
        original=load(O/'inputs/ORIGINAL_REPLAY_TASK.json');q=run('qualification_original_true_r0',dict(mode='full3d',strict_bounds=False,source_xyz=original['source_xyz']),dict(gaussian=original['gaussian_seed_words'],uniform=original['uniform_seed_words']))
        actual=rows(q/'RESPONSES.csv');expected=rows(O/'inputs/ORIGINAL_REPLAY_EXPECTED.csv');errors=[abs(float(a['raw_gas_ppm'])-float(b['raw_gas_ppm'])) for a,b in zip(actual,expected)];assert len(actual)==len(expected)==604 and max(errors)==0,'ORIGINAL_KERNEL_QUERY_REPLAY_MISMATCH'
        put(O/'ORIGINAL_KERNEL_PARITY.json',dict(status='PASS_EXACT604RAW_QUERIES',queries=604,max_abs_error_ppm=max(errors),mode='original bounds; unchanged original3D dynamics'))
        arms=[('original_bounds_full3d','full3d',False),('strict_bounds_full3d','full3d',True),('strict_bounds_plane','plane',True)]
        def campaign(selected):
            for arm,mode,strict in selected:
                for source,xyz in plan['sources'].items():
                    for pred in plan['prediction_streams']:
                        task=dict(mode=mode,strict_bounds=strict,source_xyz=xyz,prediction=pred['id'],noise_input=.05 if mode=='plane_noise' else .015,coarse_scene=str(W/'E3_ORACLE_scene.json'))
                        name=f'{arm}_{source}_{pred["id"]}';run(name,task,dict(gaussian=pred['cache_seed_words'],uniform=[pred['uniform_seed']]))
                        print(json.dumps(dict(completed=name)),flush=True)
        campaign(arms)
        schedule=rows(O/'inputs/QUERIES.csv');groups={}
        for r in schedule:
            if r['group']=='historical' and int(r['stop'])>=10:groups.setdefault((r['stop'],r['window']),[]).append(r['query_id'])
        recovery=[]
        for pred in plan['prediction_streams']:
            counts={}
            for arm in ['strict_bounds_full3d','strict_bounds_plane']:
                r={r['query_id']:float(r['raw_gas_ppm']) for r in rows(O/'runs'/f'{arm}_true_{pred["id"]}'/'RESPONSES.csv')};counts[arm]=sum(np.mean([r[k] for k in keys])>.1 for keys in groups.values())
            recovery.append(dict(prediction=pred['id'],counts=counts))
        vertical=all(r['counts']['strict_bounds_full3d']>r['counts']['strict_bounds_plane'] for r in recovery)
        additional=[('strict_bounds_no_vertical_wind','no_vwind',True),('strict_bounds_no_buoyancy','no_buoyancy',True)] if vertical else [('strict_bounds_plane_coarse_wind','plane_coarse',True),('strict_bounds_plane_native_noise','plane_noise',True)]
        put(O/'PREDECLARED_STAGE2_GATE.json',dict(vertical_effect_in_both_streams=vertical,recovery=recovery,additional_arms=additional,gate_scope='resource routing fixed in preregistration, not method tuning or significance'))
        campaign(additional);shutil.copy2(G/'cause_driver',O/'cause_driver')
        put(O/'EXECUTION_RECEIPT.json',dict(status='PASS_BOUNDED_SAME_KERNEL_CAUSAL_LADDER',candidate_calls=20,engineering_original_replays=1,additional_arms=additional,new_ROS=0,new_dataset_world_archives=0,total_wall_s=time.monotonic()-start,max_child_CPU_s=max(c['CPU_s'] for c in cost),output_bytes=sum(f.stat().st_size for f in O.rglob('*') if f.is_file()),driver_ELF_sha256=sha(G/'cause_driver'),fixed_history_actual2400steps=True,original_worlds_unchanged=True))
        print('RESULT_RECEIVED_SAME_KERNEL_CAUSAL_LADDER',flush=True)
    except Exception as e:
        stop=O/'STOP_PRESERVED.json';attempt=1
        while stop.exists():attempt+=1;stop=O/('STOP_PRESERVED_'+str(attempt)+'.json')
        put(stop,dict(reason=str(e),cost=cost,wall_s=time.monotonic()-start));raise

if __name__=='__main__':main()
