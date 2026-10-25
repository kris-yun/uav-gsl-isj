"""Sequential controlled warmup continuation. No physical world or ROS run."""
from pathlib import Path
import hashlib,json,os,resource,shutil,subprocess,time
import numpy as np

ROOT=Path('/mnt/hgfs/workspace/METHOD_COMPARISON_O24_1M2_20261024')
OUT=ROOT/'outputs/E3_HISTORY_SUPPORT_20261025'
OLD=ROOT/'outputs/E3_CAUSAL_PAIR_20261025'
G=Path('/home/zyc/ros2_ws/research_runs/e3_history_support_20261025')
FROZEN=ROOT.parent/'FROZEN_O24_1M2_SCREEN12_20261024/source_snapshot'
COMPAT=ROOT/'V11_REVIEW_20261024/function_trial/compatibility_headers'

def load(path):return json.loads(path.read_text())
def put(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def build_source():
    source=(OLD/'event_control/native_observer.cpp').read_text()
    source=source.replace('int warmsteps=0;', 'int warmsteps=0;double requested_seconds=0,warm_seconds=0;int first_exit_step=0;json first_exit_rng;float max_sigma_at_record_start=10;')
    source=source.replace('warmup=true;warmsteps=0;', 'warmup=true;warmsteps=0;first_exit_step=0;first_exit_rng=nullptr;max_sigma_at_record_start=10;')
    needle='filament.active = false;\n                        stable = true;\n                        break;'
    assert source.count(needle)==1
    source=source.replace(needle, '''filament.active = false;
                        if(Obs::first_exit_step==0){Obs::first_exit_step=count+1;Obs::first_exit_rng=Audit::end();}
                        if(Obs::requested_seconds<=0){stable=true;break;}''')
    needle='        ZoneScopedN("Recording"); Obs::warmup=false;'
    assert source.count(needle)==1
    source=source.replace('                count++;\n            }\n        }', '''                count++;
            }
            Obs::warmsteps=count;Obs::warm_seconds=count*deltaTime*2;
            for(size_t i=0;i<filaments.size();i++)if(filaments[i].active)Obs::max_sigma_at_record_start=std::max(Obs::max_sigma_at_record_start,Obs::sigma[i]);
        }''',1)
    needle='if(mode!="replay")Obs::target=out+".particles.bin";'
    assert source.count(needle)==1
    source=source.replace(needle,'Obs::requested_seconds=spec.value("history_seconds",0.);if(mode!="replay"&&spec.value("save_trace",true))Obs::target=out+".particles.bin";')
    needle='Probe probe(hg,pg,wg,s);'
    assert source.count(needle)==1
    source=source.replace(needle,'if(Obs::requested_seconds>0)s.maxWarmupIterations=std::ceil(Obs::requested_seconds/(2*s.deltaTime));'+needle)
    needle='std::ofstream o(out+".json");'
    assert source.count(needle)==1
    source=source.replace(needle,'''result["history"]={{"requested_s",Obs::requested_seconds},{"actual_warmup_steps",Obs::warmsteps},{"actual_warmup_s",Obs::warm_seconds},{"first_exit_step",Obs::first_exit_step},{"first_exit_rng",Obs::first_exit_rng},{"max_sigma_cm_at_record_start",Obs::max_sigma_at_record_start}};'''+needle)
    (OUT/'history_observer.cpp').write_text(source)

def main():
    assert not (OUT/'EXECUTION_RECEIPT.json').exists()
    G.mkdir(parents=True,exist_ok=True);(OUT/'runs').mkdir();(OUT/'logs').mkdir();build_source()
    plan=load(OUT/'PREREGISTERED_HISTORY_CONTRACT.json');cost=[];start=time.monotonic()
    def limits():resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_FSIZE,(33554432,33554432))
    def execute(name,args):
        t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
        with (OUT/'logs'/(name+'.stdout')).open('w') as so,(OUT/'logs'/(name+'.stderr')).open('w') as se:
            p=subprocess.Popen(list(map(str,args)),stdout=so,stderr=se,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),preexec_fn=limits)
            while p.poll() is None:
                if time.monotonic()-start>900 or time.monotonic()-t>120:p.kill();p.wait();raise RuntimeError('WALL_CAP')
                if sum(q.stat().st_size for q in OUT.rglob('*') if q.is_file())>134217728:p.kill();p.wait();raise RuntimeError('OUTPUT_CAP')
                time.sleep(.2)
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        cost.append(dict(stage=name,argv=list(map(str,args)),returncode=p.returncode,wall_s=time.monotonic()-t,CPU_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime));put(OUT/'COST.json',cost)
        assert p.returncode==0,(name,p.returncode)
    try:
        args=['g++','-std=gnu++17','-O3','-DNDEBUG','-include','bits/stdc++.h','-I'+str(COMPAT),'-I'+str(FROZEN/'src'),'-I'+str(FROZEN/'third_party/DDA/include'),'-I'+str(FROZEN/'third_party/xxHash/include'),OUT/'history_observer.cpp',FROZEN/'src/gsl_server/algorithms/Common/Utils/NQAQuadtree.cpp','-o',G/'history_observer']
        execute('build_history_observer',args)
        inp=OUT/'inputs';parity=[]
        for case,label in [('E3','589'),('E3','660'),('A2','true'),('A2','rival')]:
            prefix=OUT/'runs'/f'parity_{case}_{label}';spec=load(inp/f'{case}_replay_{label}.json')
            execute(prefix.name,[G/'history_observer',inp/f'{case}_scene.json','replay',inp/f'{case}_replay_{label}.json',prefix,inp/f'{case}_replay_{label}.cache.f32'])
            actual=load(prefix.with_suffix('.json'));expected=np.fromfile(inp/f'{case}_expected_{label}.f32',dtype='<f4');got=np.fromfile(prefix.with_suffix('.f32'),dtype='<f4')
            keys=['seed','state','uc','uh','gc','gh','index'];assert np.array_equal(got,expected) and all(actual['after'][k]==spec['rng']['after'][k] for k in keys)
            parity.append(dict(case=case,call=spec['candidate']['call'],map_float_count=len(got),all_floats_exact=True,RNG_endpoint_exact=True))
        put(OUT/'NATIVE_PARITY.json',parity)
        for case in ['E3','A2']:
            points=[dict(label=k,point=v) for k,v in plan['E3_sources'].items()] if case=='E3' else load(inp/'A2_PAIR.json')['points']
            for point in points:
                for pred in plan['prediction_streams']:
                    prefixes={}
                    for history in ['native','long220']:
                        name=f'{case}_{point["label"]}_{pred["id"]}_{history}';prefix=OUT/'runs'/name;prefixes[history]=prefix
                        spec=dict(arm='C' if point['label']=='true' else 'D',point=point['point'],seed=pred['uniform_seed'],history_seconds=0 if history=='native' else plan['fixed_history_s'],save_trace=case=='E3' and history=='long220')
                        put(prefix.with_suffix('.spec.json'),spec)
                        execute(name,[G/'history_observer',inp/f'{case}_scene.json','arm',prefix.with_suffix('.spec.json'),prefix,inp/(pred['id']+'.cache.f32')])
                        if case=='E3' and history=='native':
                            oldprefix=OLD/'event_control'/f'{point["label"]}_{pred["id"]}';a=load(prefix.with_suffix('.json'));b=load(oldprefix.with_suffix('.json'))
                            assert np.array_equal(np.fromfile(prefix.with_suffix('.f32'),dtype='<f4'),np.fromfile(oldprefix.with_suffix('.f32'),dtype='<f4')) and a['after']==b['after'],'BASELINE_POINT_REPLAY_FAILED'
                        if case=='E3' and history=='long220':
                            execute('kernel_'+name,[OLD/'event_control/kernel',str(prefix)+'.particles.bin',OLD/'native_runtime/OccupancyGrid3D.csv',inp/'E3_UNIQUE_POINTS.csv',inp/'E3_CONSTANTS.json',str(prefix)+'.timeseries.csv'])
                    short=load(prefixes['native'].with_suffix('.json'));long=load(prefixes['long220'].with_suffix('.json'))
                    assert short['history']['first_exit_step']==long['history']['first_exit_step']
                    assert short['history']['first_exit_rng']==long['history']['first_exit_rng'],'NOT_EXACT_SHARED_RANDOM_PREFIX'
                    assert long['history']['actual_warmup_steps']==1100
                    print(json.dumps(dict(completed=case+'_'+point['label']+'_'+pred['id'],native_warmup=short['history']['actual_warmup_s'],long_warmup=long['history']['actual_warmup_s'])),flush=True)
        shutil.copy2(G/'history_observer',OUT/'history_observer')
        put(OUT/'EXECUTION_RECEIPT.json',dict(status='PASS_NATIVE_PARITY_AND_HISTORY_INTERVENTION',native_parity=parity,new_physical_worlds=0,new_ROS=0,point_forward_calls=16,native_point_baseline_replays=8,long_history_forwards=8,engineering_native_leaf_replays=4,total_wall_s=time.monotonic()-start,max_child_CPU_s=max(r['CPU_s'] for r in cost),output_bytes=sum(q.stat().st_size for q in OUT.rglob('*') if q.is_file()),observer_source_sha256=sha(OUT/'history_observer.cpp'),observer_ELF_sha256=sha(G/'history_observer')))
        print('RESULT_RECEIVED_HISTORY_SUPPORT_INTERVENTION',flush=True)
    except Exception as error:
        put(OUT/'STOP_PRESERVED.json',dict(reason=str(error),cost=cost,wall_s=time.monotonic()-start));raise

if __name__=='__main__':main()
