from pathlib import Path
import json,hashlib,subprocess,time,os,resource,shutil
import numpy as np
B=Path('/mnt/hgfs/workspace/METHOD_COMPARISON_O24_1M2_20261024');O=B/'outputs/E3_CAUSAL_PAIR_20261025';C=B/'method_source/E3_CAUSAL_PAIR_20261025';R=B/'V12_REVIEW_20261024/pro_handoff/physical_replay_bundle';CORE=R/'gaden_core_actual_source';T=B/'V11_REVIEW_20261024/function_trial';S=Path('/mnt/hgfs/workspace/FROZEN_O24_1M2_SCREEN12_20261024/source_snapshot');G=Path('/home/zyc/ros2_ws/research_runs/e3_event_operator_20261025')
def put(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert (O/'PHYSICAL_CAMPAIGN_RECEIPT.json').exists(),'physical gate required';G.mkdir(parents=True,exist_ok=False);E=O/'event_control';E.mkdir();start=time.monotonic();cost=[];previous=load(O/'PHYSICAL_CAMPAIGN_RECEIPT.json')['total_execution_wall_s'];plan=load(O/'PREREGISTERED_CAUSAL_CONTRACT.json')
 src=(T/'native_function_runner.cpp').read_text()
 observer=r'''
namespace Obs {
std::string target;std::vector<float>sigma,mass;bool warmup;std::ofstream trace;int warmsteps=0;
void init(size_t n){sigma.assign(n,10);mass.assign(n,0);warmup=true;warmsteps=0;}
void spawn(int i,double dt){sigma[i]=10;mass[i]=10*dt/5;}
void moved(int i,double dt){sigma[i]+=15/(2*sigma[i])*dt;}
template<class F>void record(const F&filaments,int t){
 if(target.empty())return;if(!trace.is_open())trace.open(target,std::ios::binary);uint32_t step=t,count=0;for(const auto&f:filaments)count+=f.active;
 trace.write((char*)&step,4);trace.write((char*)&count,4);
 for(size_t i=0;i<filaments.size();i++)if(filaments[i].active){std::array<float,4>a={filaments[i].position.x,filaments[i].position.y,sigma[i],mass[i]};trace.write((char*)a.data(),16);}
}
void finish(){if(trace.is_open())trace.close();}
}
'''
 src=src.replace('using json=nlohmann::json;','using json=nlohmann::json;\n'+observer)
 original='std::vector<Filament> filaments(warmupLimit * numFilamentsIteration + timesteps * numFilamentsIteration);';assert original in src;src=src.replace(original,original+'\n        Obs::init(filaments.size());')
 src=src.replace('filaments[lastActivated].active = true;','filaments[lastActivated].active = true; Obs::spawn(lastActivated,deltaTime*(Obs::warmup?2:1));')
 src=src.replace('moveFilament(filament, indices, deltaTime * 2, noiseSTDev);','moveFilament(filament, indices, deltaTime * 2, noiseSTDev); Obs::moved(&filament-filaments.data(),deltaTime*2);')
 src=src.replace('moveFilament(filament, indices, deltaTime, noiseSTDev);','moveFilament(filament, indices, deltaTime, noiseSTDev); Obs::moved(&filament-filaments.data(),deltaTime);')
 src=src.replace('ZoneScopedN("Recording");','ZoneScopedN("Recording"); Obs::warmup=false;')
 marker='            for (Filament& filament : filaments)\n            {\n                if (!filament.active)\n                    continue;\n\n                // update map';assert marker in src;src=src.replace(marker,'            Obs::record(filaments,t);\n'+marker)
 marker='std::string out=argv[4];Audit::loadTable';assert marker in src;src=src.replace(marker,'std::string out=argv[4];if(mode!="replay")Obs::target=out+".particles.bin";Audit::loadTable')
 marker='auto after=Audit::end();';src=src.replace(marker,'Obs::finish();'+marker)
 (E/'native_observer.cpp').write_text(src);shutil.copy2(T/'scene.json',E/'scene.json');put(E/'OPERATOR_DEFINITION.json',dict(source='Unchanged native2D transport/center scoring plus passive birth/spread/mass observer',native_paths_per_iteration=5,physical_filaments_per_s=10,warmup_dt_s=.2,record_dt_s=.1,mass_weights='physical release10*actualstep/5 per quadrature path; .4warmup,.2record',spread='native GADEN sigma +=15/(2sigma)*dt; starts10cm',z_assumption_m=.7,LOS='unchanged native3DLOS; no bypass',units='ppm, using archived E3 native mole constants',limits='Event-matched readout on stationary2Dtransport, not full3Dphysical history; no reliable-model claim from interface parity alone'))
 def limits():resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_FSIZE,(33554432,33554432))
 def execute(name,args):
  t=time.monotonic();a=resource.getrusage(resource.RUSAGE_CHILDREN);env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1');
  with (E/(name+'.stdout')).open('w') as so,(E/(name+'.stderr')).open('w') as se:
   p=subprocess.Popen(args,stdout=so,stderr=se,env=env,preexec_fn=limits)
   while p.poll() is None:
    if previous+time.monotonic()-start>900 or time.monotonic()-t>120:p.kill();p.wait();raise RuntimeError('WALL_CAP')
    if sum(f.stat().st_size for f in O.rglob('*') if f.is_file())>134217728:p.kill();p.wait();raise RuntimeError('OUTPUT_CAP')
    time.sleep(.4)
  b=resource.getrusage(resource.RUSAGE_CHILDREN);cost.append(dict(stage=name,argv=args,returncode=p.returncode,wall_s=time.monotonic()-t,CPU_s=b.ru_utime+b.ru_stime-a.ru_utime-a.ru_stime));put(E/'COST.json',cost);assert p.returncode==0,(name,'see stderr')
 try:
  cc=['g++','-std=gnu++17','-O3','-DNDEBUG','-include','bits/stdc++.h','-I'+str(T/'compatibility_headers'),'-I'+str(S/'src'),'-I'+str(S/'third_party/DDA/include'),'-I'+str(S/'third_party/xxHash/include'),str(E/'native_observer.cpp'),str(S/'src/gsl_server/algorithms/Common/Utils/NQAQuadtree.cpp'),'-o',str(G/'native_observer')];execute('build_native_observer',cc)
  ck=['g++','-std=c++20','-O2','-DGADEN_ROS=0','-include','bits/stdc++.h','-ffunction-sections','-fdata-sections','-I'+str(CORE/'include'),'-I'+str(CORE/'third_party/DDA/include'),'-I'+str(CORE/'third_party/DDA/third_party/glm'),'-I'+str(CORE/'third_party/yaml-cpp/include'),'-I'+str(CORE/'third_party/libbsc'),str(C/'kernel.cpp')]+[str(CORE/'src'/f) for f in ['Simulation.cpp','Environment.cpp','WindSequence.cpp','GasSource.cpp']]+['-L'+str(R/'actual_runtime'),'-Wl,-rpath,'+str(R/'actual_runtime'),'-Wl,--gc-sections','-lfmt','-lyaml-cpp','-lz','-lbsc','-o',str(G/'kernel')];execute('build_kernel',ck)
  parity=[]
  for call in [589,660]:
   spec=load(T/f'replay_call_{call}.json');prefix=E/f'parity_{call}';execute('parity_'+str(call),[str(G/'native_observer'),str(E/'scene.json'),'replay',str(T/f'replay_call_{call}.json'),str(prefix),str(T/f'native_rng_states.jsonl.cache.thread{spec["rng"]["before"]["tid"]}.f32')]);a=np.fromfile(str(prefix)+'.f32',dtype='<f4');b=np.fromfile(T/f'expected_call_{call}.f32',dtype='<f4');actual=load(str(prefix)+'.json');keys=['seed','state','uc','uh','gc','gh','index'];ok=np.array_equal(a,b) and all(actual['after'][k]==spec['rng']['after'][k] for k in keys);assert ok,'NATIVE_OBSERVER_PARITY_FAIL';parity.append(dict(call=call,all2112floats_exact=True,RNG_endpoint_exact=True))
  put(E/'NATIVE_PARITY.json',parity);constants=load(O/'worlds/true_r0/GENERATOR_RESULT.json');put(E/'CONSTANTS.json',constants)
  for pred in plan['prediction_streams']:
   cache=E/(pred['id']+'.cache.f32');put(E/(pred['id']+'.json'),pred);execute('make_'+pred['id']+'_cache',[str(G/'kernel'),'cache',str(E/(pred['id']+'.json')),str(cache)])
   for source,point in [('true',[-4.,-1.9]),('rival',[-2.375,-4.875])]:
    ident=source+'_'+pred['id'];spec=dict(arm='C' if source=='true' else 'D',replicate=pred['id'],seed=pred['uniform_seed'],point=point);put(E/(ident+'.spec.json'),spec);prefix=E/ident
    execute('simulate_'+ident,[str(G/'native_observer'),str(E/'scene.json'),'arm',str(E/(ident+'.spec.json')),str(prefix),str(cache)])
    execute('kernel_'+ident,[str(G/'kernel'),str(prefix)+'.particles.bin',str(R/'actual_runtime/OccupancyGrid3D.csv'),str(O/'schedule/UNIQUE_POINTS.csv'),str(E/'CONSTANTS.json'),str(prefix)+'.timeseries.csv'])
  shutil.copy2(G/'native_observer',E/'native_observer');shutil.copy2(G/'kernel',E/'kernel');put(E/'RECEIPT.json',dict(status='PASS_EXACT_NATIVE_TRAJECTORY_PARITY_THEN_FOUR_MATCHED_EVENT_READOUTS',new_native_point_forward_calls=4,paired_physical_worlds=4,new_ROS=0,readout_only_transport_causal_control=True,same_native_trajectories_for_center_and_PID=True,code_sha256=sha(E/'native_observer.cpp'),ELF_sha256=sha(G/'native_observer'),kernel_ELF_sha256=sha(G/'kernel'),cost=cost,wall_s=time.monotonic()-start,combined_execution_wall_s=previous+time.monotonic()-start))
  print('RESULT_RECEIVED_MATCHED_EVENT_CONTROL',flush=True)
 except Exception as e:put(E/'STOP.json',dict(reason=str(e),cost=cost,wall_s=time.monotonic()-start));raise
if __name__=='__main__':main()
