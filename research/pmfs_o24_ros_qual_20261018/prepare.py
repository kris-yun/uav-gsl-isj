from pathlib import Path
import ast,datetime,difflib,hashlib,json,re,shutil
R=Path(__file__).resolve().parent
F=Path(r'D:\ZYC\UAV\.codex\worktrees\pmfs-paper-eq6-20261017\A-gas\research\pmfs_o24_baseline_freeze_20261018')
OLD=R.parent/'PMFS_EARLY_DECLARATION_AUDIT_20261018'
S='/mnt/hgfs/workspace/'+R.name;V='/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018'
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'PRECOMMIT.json').exists()
shutil.copytree(F/'o24_port_gmrf_source',R/'source_runtime',dirs_exist_ok=True)
src=R/'source_runtime';utils=src/'src/gsl_server/algorithms/Common/Utils';sim=src/'src/gsl_server/algorithms/PMFS/internal/Simulations.cpp'
header='''#pragma once
#include <cstdint>
#include <string>
namespace GSL::Utils {
struct O24Snapshot { bool ui=false,ci=false;uint32_t seed=0,state=65535;uint64_t uc=0,uh=1469598103934665603ULL,gc=0,gh=1469598103934665603ULL,nc=0,nh=1469598103934665603ULL,tid=0;int size=0,index=-1,initial=-1;std::string engine,distribution;std::string json()const;};
void O24NoteUniform(uint32_t*seed,uint32_t*state);
void O24NoteNormal(void*distribution,double value);
void O24NoteCache(uint16_t*index,const float*table,int size);
void O24NoteCacheNext(float value);
O24Snapshot O24Capture();
void O24WriteCache(const std::string&prefix);
}
'''
(utils/'O24RandomAudit.hpp').write_text(header,encoding='utf-8',newline='\n')
p=utils/'Math.hpp';t=p.read_text(encoding='utf-8');t=t.replace('#include <vector>','#include <vector>\n#include <gsl_server/algorithms/Common/Utils/O24RandomAudit.hpp>')
n='                m_precalculatedTable[i] = Utils::randomFromGaussian(0, 1);';assert t.count(n)==1;t=t.replace(n,n+'\n            O24NoteCache(&m_index,m_precalculatedTable.data(),Size);')
n='            return mean + stdev * m_precalculatedTable[m_index];';assert t.count(n)==1;t=t.replace(n,'            O24NoteCacheNext(m_precalculatedTable[m_index]);\n'+n);p.write_text(t,encoding='utf-8',newline='\n')
implementation='''
    namespace { struct O24AuditState {O24Snapshot snap;uint32_t *seed=nullptr,*state=nullptr;uint16_t *index=nullptr;const float*table=nullptr;std::normal_distribution<>*dist=nullptr;bool written=false;};
    static thread_local O24AuditState oa;static std::atomic<uint64_t> oat{0};
    uint64_t hstep(uint64_t h,uint64_t x){return (h^x)*1099511628211ULL;}}
    void O24NoteUniform(uint32_t*seed,uint32_t*state){oa.seed=seed;oa.state=state;++oa.snap.uc;oa.snap.uh=hstep(oa.snap.uh,*state);}
    void O24NoteNormal(void*distribution,double value){oa.dist=static_cast<std::normal_distribution<>*>(distribution);uint64_t b;std::memcpy(&b,&value,8);++oa.snap.nc;oa.snap.nh=hstep(oa.snap.nh,b);}
    void O24NoteCache(uint16_t*index,const float*table,int size){oa.index=index;oa.table=table;oa.snap.size=size;oa.snap.initial=*index;}
    void O24NoteCacheNext(float value){uint32_t b;std::memcpy(&b,&value,4);++oa.snap.gc;oa.snap.gh=hstep(oa.snap.gh,b);}
    O24Snapshot O24Capture(){if(!oa.snap.tid)oa.snap.tid=++oat;auto s=oa.snap;s.ui=oa.seed!=nullptr;if(s.ui){s.seed=*oa.seed;s.state=*oa.state;}s.ci=oa.index!=nullptr;if(s.ci)s.index=*oa.index;std::ostringstream e;e<<RNGengine;s.engine=e.str();if(oa.dist){std::ostringstream d;d<<std::setprecision(17)<<*oa.dist;s.distribution=d.str();}return s;}
    void O24WriteCache(const std::string&prefix){if(oa.table&&!oa.written){std::ofstream f(prefix+".thread"+std::to_string(oa.snap.tid)+".f32",std::ios::binary);if(!f)throw std::runtime_error("Cannot write RNG cache");f.write(reinterpret_cast<const char*>(oa.table),oa.snap.size*sizeof(float));if(!f)throw std::runtime_error("RNG cache write failed");oa.written=true;}}
    std::string O24Snapshot::json()const{std::ostringstream s;s<<"{\\\"ui\\\":"<<int(ui)<<",\\\"seed\\\":"<<seed<<",\\\"state\\\":"<<state<<",\\\"uc\\\":"<<uc<<",\\\"uh\\\":"<<uh<<",\\\"gc\\\":"<<gc<<",\\\"gh\\\":"<<gh<<",\\\"nc\\\":"<<nc<<",\\\"nh\\\":"<<nh<<",\\\"tid\\\":"<<tid<<",\\\"ci\\\":"<<int(ci)<<",\\\"size\\\":"<<size<<",\\\"index\\\":"<<index<<",\\\"initial\\\":"<<initial<<",\\\"engine\\\":\\\""<<engine<<"\\\",\\\"distribution\\\":\\\""<<distribution<<"\\\"}";return s.str();}
'''
p=utils/'Math.cpp';t=p.read_text(encoding='utf-8');t=t.replace('#include <chrono>','#include <chrono>\n#include <atomic>\n#include <cstring>\n#include <sstream>\n#include <fstream>\n#include <iomanip>\n#include <stdexcept>')
n='    static thread_local std::minstd_rand0 RNGengine;';assert t.count(n)==1;t=t.replace(n,n+'\n'+implementation)
n='        return mean + dist(RNGengine);';assert t.count(n)==1;t=t.replace(n,'        const double nativeValue = mean + dist(RNGengine);\n        O24NoteNormal(&dist,nativeValue);\n        return nativeValue;')
n='        state = XXHash32::hash(&state, sizeof(state), seed);';assert t.count(n)==1;t=t.replace(n,n+'\n        O24NoteUniform(&seed,&state);');p.write_text(t,encoding='utf-8',newline='\n')
t=sim.read_text(encoding='utf-8').replace('#include <atomic>','#include <atomic>\n#include <omp.h>')
n='        SimulationSource source(node, measuredHitProb.metadata);';assert t.count(n)==1;t=t.replace(n,'        const auto rngBefore = Utils::O24Capture();\n'+n)
n='        result.sourceProb = sourceProbFromMaps(measuredHitProb, result.hitMap);';assert t.count(n)==1;t=t.replace(n,n+'\n        const auto rngAfter = Utils::O24Capture();')
n='                maps.flush();rows.flush();';assert t.count(n)==1;t=t.replace(n,n+'''
                if(const char*rp=std::getenv("O24_RNG_TRACE")){static std::ofstream rng(rp);rng<<"{\\\"update\\\":"<<auditUpdate.load()<<",\\\"call\\\":"<<call<<",\\\"omp_thread\\\":"<<omp_get_thread_num()<<",\\\"origin_x\\\":"<<node->origin.x<<",\\\"origin_y\\\":"<<node->origin.y<<",\\\"size_x\\\":"<<node->size.x<<",\\\"size_y\\\":"<<node->size.y<<",\\\"before\\\":"<<rngBefore.json()<<",\\\"after\\\":"<<rngAfter.json()<<"}\\n";rng.flush();Utils::O24WriteCache(std::string(rp)+".cache");}
''');sim.write_text(t,encoding='utf-8',newline='\n')
roles=[]
for case,template in [('A2','EA18_A2_R01'),('B2','EA18_B2_R01')]:
 for i in [1,2]:
  rid=f'O24G_{case}_R{i:02d}';domain=224+len(roles);out=R/'cases'/rid;out.mkdir(parents=True,exist_ok=True);old=OLD/'cases'/template;oldT='/home/zyc/ros2_ws/pmfs_early_declaration_20261018/cases/'+template;oldRun='/mnt/hgfs/workspace/'+OLD.name+'/cases/'+template+'/runtime';T=V+'/cases/'+rid;runtime=S+'/cases/'+rid+'/runtime'
  m=json.loads((old/'CASE_META.json').read_text(encoding='utf-8'));m.update(baseline_identity='PMFS-O24-PORT-GMRF',audit_profile='O24_NATIVE_RULES_LOCAL_GMRF',ROS_DOMAIN_ID=domain,actual_binary_sha256='NOT_BUILT_YET',RNG_policy='Native time-initialized thread state captured per candidate and stream-replay validated; no forced seed',source_probability_and_planning_formulas_changed=False)
  m['expected_parameters'].update(sourceDiscriminationPower=.2,convergence_thr=1.5);m['audit_setting']['id']=rid;m['audit_setting']['convergence_variance_m2']=1.5;m['player']['r7_frame_time_csv']=T+'/AUTHOR_WALL_FILE_CADENCE.csv';m['player']['r7_clock_trace_path']=runtime+'/physical_clock_trace.csv';put(out/'CASE_META.json',m)
  for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','AUTHOR_WALL_FILE_CADENCE.csv']:
   s=(old/name).read_text(encoding='utf-8').replace(oldT,T).replace(oldRun,runtime).replace(template,rid).replace('/home/zyc/ros2_ws/pmfs_early_declaration_20261018/gsl_actionserver_node',V+'/gsl_actionserver_node')
   d=219 if case=='A2'else 221;s=s.replace('ROS_DOMAIN_ID='+str(d),'ROS_DOMAIN_ID='+str(domain)).replace("ROS_DOMAIN_ID='"+str(d)+"'","ROS_DOMAIN_ID='"+str(domain)+"'")
   if name=='N1_launch.py':s=s.replace('{"sourceDiscriminationPower": 1.0}','{"sourceDiscriminationPower": 0.2}').replace('{"convergence_thr": 1.0}','{"convergence_thr": 1.5}')
   if name=='runtime_driver.py':
    n="os.environ['NATIVE_PMFS_CANDIDATE_AUDIT']=str(R/'native_candidate_maps')";assert n in s;s=s.replace(n,n+"\nos.environ['O24_RNG_TRACE']=str(R/'native_rng_states.jsonl')")
   (out/name).write_text(s,encoding='utf-8',newline='\n')
   if name.endswith('.py'):ast.parse(s)
  roles.append(dict(id=rid,case=case,repeat=i,domain=domain,guest_path=T,runtime_shared=runtime))
patches=[];(R/'patches').mkdir(exist_ok=True)
for p in sorted(src.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(src);before=F/'o24_port_gmrf_source'/rel
 if not before.exists()or before.read_bytes()!=p.read_bytes():
  old=before.read_text(encoding='utf-8')if before.exists()else'';new=p.read_text(encoding='utf-8');diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='stage0/'+rel.as_posix(),tofile='rng-recording/'+rel.as_posix()));dest=R/'patches'/(rel.as_posix().replace('/','__')+'.patch');dest.write_text(diff,encoding='utf-8');patches.append(dict(path=rel.as_posix(),sha256=sha(p),classification='RNG_STATE_RECORDING_ONLY_NO_SEED_OVERRIDE'))
put(R/'PRECOMMIT.json',dict(user_authorization='2026-10-18 user explicitly approved O24 ROS build, RNG recording qualification and A2/B2 two runs each; no AIMMD',roles=roles,primary_goals=4,technical_retry_cap=0,total_goal_cap=4,total_batch_wall_s=2400,max_goal_wall_s=420,guest_free_floor_bytes=5*2**30,host_free_floor_bytes=2*2**30,new_worlds=0,AIMMD=0,parameters=json.loads((R/'cases/O24G_A2_R01/CASE_META.json').read_text(encoding='utf-8'))['expected_parameters'],RNG='Keep native initialization; record actual seed/state/cachephase/candidateowner and validate stream replay. No claim of deterministic future action trajectory.',patches_from_stage0=patches,source_files=[dict(path=p.relative_to(src).as_posix(),sha256=sha(p))for p in sorted(src.rglob('*'))if p.is_file()]))
put(R/'AUTHORIZATION_AND_SCOPE.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorized=True,goals=4,scientific_parameters_tuned=False,AIMMD=False))
shutil.copyfile(F/'UPSTREAM_SOURCE_LOCK.json',R/'UPSTREAM_SOURCE_LOCK.json');shutil.copyfile(F/'PHASE1_DIAGNOSTIC_SOURCE_PAIRS.json',R/'PHASE1_DIAGNOSTIC_SOURCE_PAIRS.json')
print(json.dumps(dict(status='O24_BUILD_AND_FOUR_ROLES_PREPARED_RNG_GATE_REQUIRED',source_files=len(list(src.rglob('*.cpp'))),roles=roles)))
