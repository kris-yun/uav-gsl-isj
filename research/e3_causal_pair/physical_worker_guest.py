"""One sequential budgeted physical campaign; stop on qualification/budget failure."""
from pathlib import Path
import csv,json,hashlib,os,resource,subprocess,time,shutil,struct,zlib
import numpy as np
B=Path('/mnt/hgfs/workspace/METHOD_COMPARISON_O24_1M2_20261024');O=B/'outputs/E3_CAUSAL_PAIR_20261025';C=B/'method_source/E3_CAUSAL_PAIR_20261025';R=B/'V12_REVIEW_20261024/pro_handoff/physical_replay_bundle';CORE=R/'gaden_core_actual_source';G=Path('/home/zyc/ros2_ws/research_runs/e3_causal_pair_20261025')
def put(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open()))
def table(p,rs):
 with Path(p).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rs[0]);w.writeheader();w.writerows(rs)
def rng_header():
 p=G/'include/gaden/internal/MathUtils.hpp';p.parent.mkdir(parents=True,exist_ok=True)
 src=(CORE/'include/gaden/internal/MathUtils.hpp').read_text();src=src.replace('#include <random>','#include <random>\n#include <fstream>\n#include <sstream>\n#include <cstdlib>\n#include <iomanip>')
 begin=src.index('    // thread-safe');end=src.index('    inline bool Approx',begin)
 patch=r'''
    struct E3Stream {
        std::mt19937 engine;
        std::normal_distribution<> normal{0,1};
        std::uniform_real_distribution<float> uniform{0.f,1.f};
        uint64_t draws=0;std::string name;
        E3Stream(std::string n):name(n){
            const char* v=std::getenv(("E3_"+name+"_WORDS").c_str());
            if(v){std::stringstream s(v);std::string w;std::vector<uint32_t>a;while(std::getline(s,w,','))a.push_back(std::stoul(w));std::seed_seq seed(a.begin(),a.end());engine.seed(seed);}
            log("initial");
        }
        void log(const std::string&phase){if(const char*p=std::getenv("E3_RNG_TRACE")){std::ofstream f(std::string(p)+"."+name+"."+phase+".txt");f<<std::setprecision(17)<<engine<<"\nnormal="<<normal<<"\nuniform="<<uniform<<"\ndraws="<<draws<<'\n';}}
        ~E3Stream(){log("final");}
    };
    inline E3Stream& e3Gaussian(){static thread_local E3Stream s("GAUSSIAN");return s;}
    inline E3Stream& e3Uniform(){static thread_local E3Stream s("UNIFORM");return s;}
    inline float GaussianRandom(float mean,float stdDev){auto&s=e3Gaussian();s.draws++;return mean+s.normal(s.engine)*stdDev;}
    inline float uniformRandom(float min,float max){auto&s=e3Uniform();s.draws++;return min+s.uniform(s.engine)*(max-min);}
'''
 src=src[:begin]+patch+src[end:]
 src=src.replace('m_precalculatedTable[i] = GaussianRandom(0, 1);','m_precalculatedTable[i] = GaussianRandom(0, 1);\n            if(const char*p=std::getenv("E3_RNG_TRACE")){std::ofstream f(std::string(p)+".cache.f32",std::ios::binary);f.write((char*)m_precalculatedTable.data(),Size*sizeof(float));std::ofstream i(std::string(p)+".cache.initial.txt");i<<"index="<<m_index<<" size="<<Size<<"\\n";}')
 # Avoid escaped quotes in actual emitted JSON.
 src=src.replace('\\\\\\"','\\"')
 src=src.replace('float nextValue(float mean, float stdev)','~PrecalculatedGaussian(){if(const char*p=std::getenv("E3_RNG_TRACE")){std::ofstream f(std::string(p)+".cache.final.txt");f<<"index="<<m_index<<" calls="<<e3Calls<<"\\n";}}\n\n        float nextValue(float mean, float stdev)')
 src=src.replace('m_index = (m_index + 1) % Size;','m_index = (m_index + 1) % Size; ++e3Calls;')
 src=src.replace('uint16_t m_index;','uint64_t e3Calls=0;\n        uint16_t m_index;')
 p.write_text(src);shutil.copy2(p,O/'provenance/MathUtils.instrumented.hpp')
def unpack(p):
 b=Path(p).read_bytes();assert b[:13]==b'GADEN_RESULT\0' and b[13]==1;a=zlib.decompress(b[22:]);n=struct.unpack_from('<Q',a,48)[0];off=56+n+28;ml=struct.unpack_from('<Q',a,off)[0];off+=8+ml;nf=struct.unpack_from('<Q',a,off)[0];v=np.frombuffer(a,dtype='<f4',offset=off+8).reshape(-1,4);assert len(v)==nf;return a,v
def main():
 assert not (O/'PHYSICAL_CAMPAIGN_RECEIPT.json').exists();G.mkdir(parents=True,exist_ok=True);rng_header();plan=load(O/'PREREGISTERED_CAUSAL_CONTRACT.json');cost=load(O/'execution/COST.json') if (O/'execution/COST.json').exists() else [];start=time.monotonic()-sum(c['wall_s'] for c in cost);(O/'execution').mkdir(exist_ok=True)
 def limits():resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_FSIZE,(16777216,16777216))
 def execute(name,args,extra=None):
  env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1');env.update(extra or {});before=resource.getrusage(resource.RUSAGE_CHILDREN);t=time.monotonic();out=O/'execution';name=name+'_attempt'+str(1+sum(c['stage'].startswith(name+'_attempt') for c in cost))
  with (out/(name+'.stdout')).open('w') as so,(out/(name+'.stderr')).open('w') as se:
   p=subprocess.Popen(args,stdout=so,stderr=se,env=env,preexec_fn=limits)
   while p.poll() is None:
    if time.monotonic()-start>900:p.kill();p.wait();raise RuntimeError('TOTAL_WALL_CAP')
    if time.monotonic()-t>120:p.kill();p.wait();raise RuntimeError('PROCESS_WALL_SAFETY_CAP')
    size=sum(f.stat().st_size for f in O.rglob('*') if f.is_file())
    if size>134217728:p.kill();p.wait();raise RuntimeError('NEW_OUTPUT_BYTE_CAP')
    time.sleep(.3)
  after=resource.getrusage(resource.RUSAGE_CHILDREN);cost.append(dict(stage=name,argv=list(map(str,args)),exit_code=p.returncode,wall_s=time.monotonic()-t,CPU_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime));put(O/'execution/COST.json',cost);assert p.returncode==0,(name,'see preserved stderr')
  return cost[-1]
 try:
  compiler=['g++','-std=c++20','-O2','-DGADEN_ROS=0','-DGPU_ACCELERATION=0','-include','bits/stdc++.h','-ffunction-sections','-fdata-sections','-fopenmp','-I'+str(G/'include'),'-I'+str(CORE/'include'),'-I'+str(CORE/'third_party/DDA/include'),'-I'+str(CORE/'third_party/DDA/third_party/glm'),'-I'+str(CORE/'third_party/yaml-cpp/include'),'-I'+str(CORE/'third_party/libbsc'),str(C/'physics.cpp')]
  compiler += [str(CORE/'src'/f) for f in ['Simulation.cpp','PlaybackSimulation.cpp','RunningSimulation.cpp','Environment.cpp','WindSequence.cpp','GasSource.cpp']]
  compiler += ['-L'+str(R/'actual_runtime'),'-Wl,-rpath,'+str(R/'actual_runtime'),'-Wl,--gc-sections','-lfmt','-lyaml-cpp','-lz','-lbsc','-o',str(G/'physics')]
  execute('build_physics',compiler);put(O/'provenance/BUILD_IDENTITY.json',dict(command=compiler,ELF_sha256=sha(G/'physics'),core_source_sha256=sha(CORE/'src/RunningSimulation.cpp'),original_library_sha256=sha(R/'actual_runtime/libgaden.so'),source_transport_body_changed=False,adaptations=['RNG initialization/state/cache trace','headless driver','selective native-format serialization; no physical changes']))
  map_path=R/'actual_runtime/OccupancyGrid3D.csv';wind=Path('/home/zyc/pmfs_e3_native_validation_20261009/one_realization_E3/wind')
  assert sha(map_path)=='24cc18fb1b428bd12d53de22e6434560f9fa34d28798d0f19b372ba9f2c8e403';assert sha(next(wind.iterdir()))=='135690ce4679f43bb02d7d40fe39b338a250f2aa94cf3e71d0f2dbf8bbe4705a'
  # A real default-state replay of E4 validates unchanged native physics and RNG
  # consumption before any independent new-world run is allowed.
  qualification=O/'generator_qualification';qualification.mkdir(exist_ok=True);assert not (qualification/'saved_world').exists(),'NO_OVERWRITE_PARTIAL_PHYSICAL_OUTPUT';qtime=rows(B.parent/'NATIVE_PMFS_FULL20_20261014/cases/E4/PHYSICAL_FRAME_TIME.csv')[:11]
  qr=[dict(query_id='q'+r['frame'],point_id=0,physical_s=r['physical_snapshot_time_s'],x=-1.,y=-.9,z=1.) for r in qtime];table(qualification/'QUERIES.csv',qr)
  task=dict(source_xyz=[-1.,-.9,1.],duration_s=6.,query_csv=str(qualification/'QUERIES.csv'));put(qualification/'TASK.json',task)
  execute('qualify_default_replay',[str(G/'physics'),'generate',str(qualification/'TASK.json'),str(map_path),str(wind),str(qualification)],dict(E3_RNG_TRACE=str(qualification/'RNG')))
  new=rows(qualification/'RESPONSES.csv');oldworld=B.parent/'NATIVE_PMFS_FULL20_20261014/cases/E4/one_realization';comparison=[]
  for i,row in enumerate(new):
   old,v=unpack(oldworld/('iteration_'+qtime[i]['frame']));newbody,vv=unpack(qualification/'saved_world'/('iteration_'+row['frame']))
   err=float(np.max(abs(v-vv))) if v.shape==vv.shape and len(v) else 0 if v.shape==vv.shape else 1e30
   comparison.append(dict(old_frame=int(qtime[i]['frame']),new_frame=int(row['frame']),count_old=len(v),count_new=len(vv),max_filament_float_error=err,payload_exact=old==newbody));assert err<1e-5,'NATIVE_GENERATOR_DEFAULT_REPLAY_MISMATCH'
  put(qualification/'PARITY.json',dict(status='PASS_NATIVE_DEFAULT_REPLAY',comparisons=comparison))
  # Existing E3 decomposition uses untouched saved states, not the new worlds.
  execute('decompose_original_E3',[str(G/'physics'),'decompose',str(O/'schedule/ORIGINAL_NATIVE_QUERY_INPUT.csv'),str(map_path),'/home/zyc/pmfs_e3_native_validation_20261009/one_realization_E3',str(O/'original_E3_decomposition')])
  for world in plan['worlds']:
   target=O/'worlds'/world['id'];target.mkdir(parents=True);task=dict(**world,duration_s=240.,query_csv=str(O/'schedule/QUERIES.csv'));put(target/'TASK.json',task)
   env=dict(E3_RNG_TRACE=str(target/'RNG'),E3_GAUSSIAN_WORDS=','.join(map(str,world['gaussian_seed_words'])),E3_UNIFORM_WORDS=','.join(map(str,world['uniform_seed_words'])))
   execute('generate_'+world['id'],[str(G/'physics'),'generate',str(target/'TASK.json'),str(map_path),str(wind),str(target)],env)
   # Re-read every queried snapshot through the existing unmodified native reader.
   rs=rows(target/'RESPONSES.csv');inp=[dict(query_id=r['query_id'],frame=r['frame'],x=r['x'],y=r['y'],z=r['z']) for r in rs];table(target/'NATIVE_REPLAY_INPUT.csv',inp)
   cmd=[str(R/'headless_build/headless_saved_query'),str(map_path),str(target/'saved_world')]
   with (target/'NATIVE_REPLAY_INPUT.csv').open() as fi,(target/'NATIVE_REPLAY_OUTPUT.csv').open('w') as fo:
    s=subprocess.run(cmd,stdin=fi,stdout=fo,stderr=subprocess.PIPE,text=True,env=dict(os.environ,OMP_NUM_THREADS='1'),timeout=90,preexec_fn=limits)
   assert s.returncode==0,s.stderr;back=rows(target/'NATIVE_REPLAY_OUTPUT.csv');errors=[abs(float(a['raw_gas_ppm'])-float(b['raw_gas_ppm'])) for a,b in zip(rs,back)];assert len(rs)==len(back)==604 and max(errors)==0
   put(target/'REPLAY_QA.json',dict(status='PASS_EXACT_NATIVE_RESERIALIZED_READOUT',queries=len(rs),max_abs_error_ppm=max(errors)))
   print(json.dumps(dict(completed=world['id'],cost=cost[-1])),flush=True)
  (O/'native_runtime').mkdir();shutil.copy2(G/'physics',O/'native_runtime/physics');shutil.copy2(map_path,O/'native_runtime/OccupancyGrid3D.csv');shutil.copy2(R/'actual_runtime/libbsc.so',O/'native_runtime/libbsc.so')
  put(O/'PHYSICAL_CAMPAIGN_RECEIPT.json',dict(status='PASS_QUALIFIED_FOUR_PAIRED_NATIVE_WORLDS',worlds=4,total_execution_wall_s=time.monotonic()-start,output_bytes=sum(p.stat().st_size for p in O.rglob('*') if p.is_file()),cost=cost,ROS_runs=0,old_worlds_modified=False,source_height_m=.7,independence_scope='Separate entropy-seeded MT engines and1000value caches, serial deterministic consumption; cyclic correlation retained within each world.'))
  print('RESULT_RECEIVED_FOUR_WORLDS',flush=True)
 except Exception as e:
  put(O/'PHYSICAL_STOP_RECEIPT.json',dict(status='STOP_PRESERVE_FIRST_FAILURE',reason=str(e),cost=cost,wall_s=time.monotonic()-start));raise
if __name__=='__main__':main()
