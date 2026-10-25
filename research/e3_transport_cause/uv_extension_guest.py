"""Four predeclared height-coupled-uv ablations, no extra scenario search."""
from pathlib import Path
import hashlib,json,os,resource,shutil,subprocess,time
import numpy as np
from worker_guest import B,P,O,W,C,G,load,put,rows,sha

def main():
    assert (O/'PREREGISTERED_UV_EXTENSION.json').exists() and not (O/'UV_EXTENSION_RECEIPT.json').exists()
    previous=load(O/'EXECUTION_RECEIPT.json');cost=[];start=time.monotonic();plan=load(O/'PREREGISTERED_CAUSAL_CONTRACT.json')
    def limits():resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_FSIZE,(16777216,16777216))
    def execute(name,args,envextra=None):
        assert not (O/'logs'/(name+'.stdout')).exists();a=resource.getrusage(resource.RUSAGE_CHILDREN);t=time.monotonic();env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1');env.update(envextra or {})
        with (O/'logs'/(name+'.stdout')).open('w') as so,(O/'logs'/(name+'.stderr')).open('w') as se:
            p=subprocess.Popen(list(map(str,args)),stdout=so,stderr=se,env=env,preexec_fn=limits)
            while p.poll() is None:
                if previous['total_wall_s']+time.monotonic()-start>900 or time.monotonic()-t>120:p.kill();p.wait();raise RuntimeError('WALL_CAP')
                if sum(f.stat().st_size for f in O.rglob('*') if f.is_file())>134217728:p.kill();p.wait();raise RuntimeError('OUTPUT_CAP')
                time.sleep(.2)
        b=resource.getrusage(resource.RUSAGE_CHILDREN);cost.append(dict(stage=name,argv=list(map(str,args)),returncode=p.returncode,wall_s=time.monotonic()-t,CPU_s=b.ru_utime+b.ru_stime-a.ru_utime-a.ru_stime));put(O/'UV_COST.json',cost);assert p.returncode==0,(name,p.returncode)
    try:
        args=next(c['argv'] for c in load(O/'COST.json') if c['stage'].startswith('build_cause_driver') and c['returncode']==0);args=list(args);args[-1]=str(G/'cause_driver_uv');execute('build_fixed_uv_driver',args)
        def run(name,task,pred):
            d=O/'runs'/name;d.mkdir();put(d/'TASK.json',task);env=dict(E3_CAUSE_MODE=task['mode'],E3_CAUSE_STRICT_BOUNDS='1',E3_GAUSSIAN_WORDS=','.join(map(str,pred['cache_seed_words'])),E3_UNIFORM_WORDS=str(pred['uniform_seed']),E3_RNG_TRACE=str(d/'RNG'))
            execute(name,[G/'cause_driver_uv',d/'TASK.json',O/'inputs/OccupancyGrid3D.csv',O/'inputs/wind_iteration_0',O/'inputs/QUERIES.csv',d],env);assert load(d/'RESULT.json')['outside_particle_time_samples']==0
            return d
        parity=[]
        for pred in plan['prediction_streams']:
            old=O/'runs'/f'strict_bounds_full3d_true_{pred["id"]}';task=load(old/'TASK.json');d=run('UV_parity_full3d_true_'+pred['id'],task,pred);a=rows(d/'RESPONSES.csv');b=rows(old/'RESPONSES.csv');assert all(x['raw_gas_ppm']==y['raw_gas_ppm'] for x,y in zip(a,b)) and len(a)==len(b)==604
            assert sha(d/'RNG.cache.final.txt')==sha(old/'RNG.cache.final.txt');parity.append(dict(prediction=pred['id'],all604ppm_exact=True,RNG_endpoint_exact=True))
        for source,xyz in plan['sources'].items():
            for pred in plan['prediction_streams']:
                task=dict(mode='fixed_uv',strict_bounds=True,source_xyz=xyz,prediction=pred['id'],noise_input=.015,coarse_scene=str(W/'E3_ORACLE_scene.json'))
                run(f'strict_bounds_fixed_uv_{source}_{pred["id"]}',task,pred);print(json.dumps(dict(completed=source+'_'+pred['id'])),flush=True)
        shutil.copy2(G/'cause_driver_uv',O/'cause_driver_uv');put(O/'UV_EXTENSION_RECEIPT.json',dict(status='PASS_FIXED_UV_HEIGHT_ABLATION',candidate_calls=4,exact_baseline_replays=parity,total_wall_s=time.monotonic()-start,cumulative_execution_wall_s=previous['total_wall_s']+time.monotonic()-start,max_child_CPU_s=max(c['CPU_s'] for c in cost),driver_ELF_sha256=sha(G/'cause_driver_uv'),new_target_worlds=0,new_ROS=0));print('RESULT_RECEIVED_FIXED_UV_ABLATION',flush=True)
    except Exception as e:put(O/'UV_STOP_PRESERVED.json',dict(reason=str(e),cost=cost,wall_s=time.monotonic()-start));raise

if __name__=='__main__':main()
