"""Bounded horizontal-wind substitution; archived-world oracle only."""
from pathlib import Path
import csv,hashlib,json,os,resource,shutil,struct,subprocess,time
import numpy as np

B=Path('/mnt/hgfs/workspace/METHOD_COMPARISON_O24_1M2_20261024')
P=B/'outputs/E3_CAUSAL_PAIR_20261025';H=B/'outputs/E3_HISTORY_SUPPORT_20261025';O=B/'outputs/E3_HORIZONTAL_WIND_ORACLE_20261025'
C=B/'method_source/E3_HORIZONTAL_WIND_ORACLE_20261025';G=Path('/home/zyc/ros2_ws/research_runs/e3_wind_oracle_20261025');CORE=P/'build_source/gaden_core'

def load(p):return json.loads(p.read_text())
def rows(p):return list(csv.DictReader(p.open()))
def put(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def qualify():
    scene=load(O/'inputs/E3_scene.json');oracle=load(O/'E3_ORACLE_scene.json');native=load(O/'NATIVE_WIND_EXPORT_QA.json');data=rows(O/'REFERENCE_WIND_SAMPLING.csv');raw=(O/'inputs/wind_iteration_0').read_bytes();version=struct.unpack('<2i',raw[:8]);assert version[0]>=2
    wind=np.frombuffer(raw,dtype='<f4',offset=8).reshape(-1,3);assert len(wind)==native['numCells'];dims=np.array(native['dimensions']);origin=np.array(native['fine_min_coord'],np.float32);cs=np.float32(native['fine_cell_size'])
    assert len(data)==scene['nx']*scene['ny']==2112
    for r in data:
        xyz=np.array([float(r[k]) for k in ['x','y','z']],np.float32);idx=((xyz-origin)/cs).astype(int);assert np.array_equal(idx,[int(r[k]) for k in ['voxel_i','voxel_j','voxel_k']]);flat=int(idx[0]+dims[0]*(idx[1]+dims[1]*idx[2]));assert flat==int(r['voxel_flat'])
        v=np.array([float(r[k]) for k in ['reference_u','reference_v','reference_w']],np.float32);assert np.array_equal(v,wind[flat]);assert np.array_equal(v[:2],np.array(oracle['wind_xy'][int(r['flat'])],np.float32))
    assert all(scene[k]==oracle[k] for k in scene if k!='wind_xy') and set(scene)==set(oracle)
    q=np.array(scene['occupancy'])==0;a=np.array(scene['wind_xy'],np.float32)[q];v=np.array(oracle['wind_xy'],np.float32)[q];vertical=np.array([float(r['reference_w']) for r in data])[q]
    for point in [[-4.,-1.9],[-2.375,-4.875]]:
        ij=((np.array(point)-scene['origin'])/scene['cell_size']).astype(int);flat=int(ij[0]+scene['nx']*ij[1]);assert scene['occupancy'][flat]==0;assert int(data[flat]['native3D_cell_state'])==0,'SOURCE_REFERENCE_COARSE_CENTER_NOT_PHYSICALLY_FREE'
    result=dict(status='PASS_NATIVE_PARSER_AND_INDEPENDENT_RAW_DECODER',native_and_independent_wind_samples_exact=2112,only_scene_wind_xy_changed=True,physical_wind_version=version,physical_wind_sha256=sha(O/'inputs/wind_iteration_0'),source_coarse_centers_physically_free=True,coarse_free_center_mismatches=native['native3D_nonfree_centers_with_PMFS_free'],mismatches_not_filled_or_unmasked=True,coarse_free_cells=int(q.sum()),horizontal_difference_RMS_mps=float(np.sqrt(np.mean(np.sum((a-v)**2,axis=1)))),GMRF_horizontal_RMS_mps=float(np.sqrt(np.mean(np.sum(a*a,axis=1)))),reference_horizontal_RMS_mps=float(np.sqrt(np.mean(np.sum(v*v,axis=1)))),reference_vertical_RMS_mps=float(np.sqrt(np.mean(vertical**2))),height_query_m=.7,projection_scope='native voxel value at coarse center; not exact continuous2D flow or all3D trajectories')
    put(O/'WIND_INPUT_QUALIFICATION.json',result)

def main():
    assert not (O/'EXECUTION_RECEIPT.json').exists();G.mkdir(parents=True,exist_ok=True);(O/'logs').mkdir();(O/'runs').mkdir();cost=[];start=time.monotonic();plan=load(O/'PREREGISTERED_WIND_CONTRACT.json')
    def limits():resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_FSIZE,(33554432,33554432))
    def execute(name,args):
        t=time.monotonic();a=resource.getrusage(resource.RUSAGE_CHILDREN)
        with (O/'logs'/(name+'.stdout')).open('w') as so,(O/'logs'/(name+'.stderr')).open('w') as se:
            p=subprocess.Popen(list(map(str,args)),stdout=so,stderr=se,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),preexec_fn=limits)
            while p.poll() is None:
                if time.monotonic()-start>900 or time.monotonic()-t>120:p.kill();p.wait();raise RuntimeError('WALL_CAP')
                if sum(f.stat().st_size for f in O.rglob('*') if f.is_file())>134217728:p.kill();p.wait();raise RuntimeError('OUTPUT_CAP')
                time.sleep(.2)
        b=resource.getrusage(resource.RUSAGE_CHILDREN);cost.append(dict(stage=name,argv=list(map(str,args)),returncode=p.returncode,wall_s=time.monotonic()-t,CPU_s=b.ru_utime+b.ru_stime-a.ru_utime-a.ru_stime));put(O/'COST.json',cost);assert p.returncode==0,(name,p.returncode)
    try:
        args=['g++','-std=c++20','-O2','-DGADEN_ROS=0','-include','bits/stdc++.h','-ffunction-sections','-fdata-sections','-I'+str(CORE/'include'),'-I'+str(CORE/'third_party/DDA/third_party/glm'),'-I'+str(CORE/'third_party/yaml-cpp/include'),C/'export_wind.cpp',CORE/'src/Environment.cpp',CORE/'src/WindSequence.cpp','-Wl,--gc-sections','-lfmt','-lyaml-cpp','-o',G/'export_wind']
        execute('build_export_wind',args)
        execute('native_export',[G/'export_wind',O/'inputs/E3_scene.json',O/'inputs/OccupancyGrid3D.csv',O/'inputs/wind_iteration_0',O]);qualify()
        model=H/'history_observer';assert sha(model)==load(H/'EXECUTION_RECEIPT.json')['observer_ELF_sha256']
        for source,point in plan['sources'].items():
            for pred in plan['prediction_streams']:
                cache=O/'inputs'/(pred['id']+'.cache.f32');name=f'{source}_{pred["id"]}';expected=load(O/'inputs'/f'control_E3_{name}_long220.json');spec=O/'inputs'/f'control_E3_{name}_long220.spec.json'
                # Exact fixed220 GMRF replay before evaluating replacement wind.
                prefix=O/'runs'/('control_'+name);execute('replay_'+name,[model,O/'inputs/E3_scene.json','arm',spec,prefix,cache])
                actual=load(prefix.with_suffix('.json'));assert actual['after']==expected['after'] and np.array_equal(np.fromfile(prefix.with_suffix('.f32'),dtype='<f4'),np.fromfile(O/'inputs'/f'control_E3_{name}_long220.f32',dtype='<f4')),'GMRF_CONTROL_REPLAY_MISMATCH'
                prefix=O/'runs'/('oracle_'+name);execute('oracle_'+name,[model,O/'E3_ORACLE_scene.json','arm',spec,prefix,cache]);record=load(prefix.with_suffix('.json'));assert record['before']==expected['before'] and record['history']['actual_warmup_steps']==1100
                execute('kernel_'+name,[P/'event_control/kernel',str(prefix)+'.particles.bin',O/'inputs/OccupancyGrid3D.csv',O/'inputs/E3_UNIQUE_POINTS.csv',O/'inputs/E3_CONSTANTS.json',str(prefix)+'.timeseries.csv'])
                print(json.dumps(dict(completed=name,oracle_score=record['score'],GMRF_score=expected['score'])),flush=True)
        shutil.copy2(G/'export_wind',O/'export_wind');shutil.copy2(model,O/'history_observer');shutil.copy2(P/'event_control/kernel',O/'PID_kernel')
        put(O/'EXECUTION_RECEIPT.json',dict(status='PASS_ONE_WIND_INPUT_INTERVENTION',existing_GMRF_exact_replays=4,new_oracle_point_forwards=4,new_worlds=0,new_ROS=0,neural_training=0,total_wall_s=time.monotonic()-start,max_child_CPU_s=max(c['CPU_s'] for c in cost),output_bytes=sum(f.stat().st_size for f in O.rglob('*') if f.is_file()),unchanged_model_ELF_sha256=sha(model),native_export_ELF_sha256=sha(G/'export_wind'),PID_kernel_ELF_sha256=sha(P/'event_control/kernel'),all_initial_states_equal=True,all_actual_warmup_steps=1100))
        print('RESULT_RECEIVED_HORIZONTAL_WIND_ORACLE',flush=True)
    except Exception as error:put(O/'STOP_PRESERVED.json',dict(reason=str(error),cost=cost,wall_s=time.monotonic()-start));raise

if __name__=='__main__':main()
