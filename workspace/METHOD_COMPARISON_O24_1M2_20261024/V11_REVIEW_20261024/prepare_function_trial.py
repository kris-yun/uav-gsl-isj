from pathlib import Path
import bisect,csv,hashlib,json,shutil
import numpy as np

B=Path(__file__).resolve().parent
F=B.parents[1]/'FROZEN_O24_1M2_SCREEN12_20261024'
# Both directories are siblings under workspace, not nested in the method tree.
F=Path('D:/ZYC/A-gas/workspace/FROZEN_O24_1M2_SCREEN12_20261024')
S=F/'source_snapshot'
I=B/'native_E3_raw'
T=B/'function_trial';assert not T.exists();T.mkdir()
def js(p):return json.loads(p.read_text(encoding='utf-8'))
def csvs(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raw=js(I/'runtime/resolved_GSL_parameters.json')
P={k:v[{1:'bool_value',2:'integer_value',3:'double_value',4:'string_value'}[v['type']]] for k,v in zip(raw['names'],raw['values'])}
nav=js(I/'runtime/NAVIGATION_MAP_METADATA.json')
post=[r for r in csvs(I/'runtime/native_posterior_updates.csv') if int(r['update'])==4]
nx=nav['width']//P['scale'];ny=nav['height']//P['scale'];cell=float(post[0]['cell_size_m'])
occ=np.ones(nx*ny,dtype=np.int32);wind=np.zeros((nx*ny,2),dtype=np.float32);logodds=np.zeros(nx*ny);confidence=np.zeros(nx*ny)
for r in post:
 k=int(r['col'])+int(r['row'])*nx;occ[k]=0;wind[k]=float(r['estimated_wind_u']),float(r['estimated_wind_v']);logodds[k]=float(r['hit_log_odds']);confidence[k]=float(r['hit_confidence'])
path=js(I/'runtime/robot_path.json');times=[p[0] for p in path]
windows=[r for r in csvs(I/'runtime/native_window_consumption.csv') if r['status']=='CONSUMED']
stops=[]
for j in range(0,len(windows),5):
 w=windows[j:j+5];coords=[]
 for e in w:
  pose=path[max(0,bisect.bisect_right(times,int(e['node_clock_ns'])*1e-9)-1)]
  coords.append([int((pose[1]-nav['origin_x'])/cell),int((pose[2]-nav['origin_y'])/cell)])
 assert len(set(map(tuple,coords)))==1
 stops.append({'stop':j//5+1,'cell':coords[0],'hits':sum(float(e['concentration_mean_ppm'])>P['th_gas_present'] for e in w),'n':len(w)})
maps=csvs(I/'runtime/native_candidate_maps.csv');rng=[json.loads(s) for s in (I/'runtime/native_rng_states.jsonl').read_text().splitlines()]
for cache in (I/'runtime').glob('native_rng_states.jsonl.cache.thread*.f32'):shutil.copyfile(cache,T/cache.name)
for call in [589,660]:
 r=next(x for x in maps if int(x['call'])==call)
 # Full f32 was retained in the original V11 payload and matched the raw evidence archive.
 data=(B/'input_package/PMFS_V11/research_v11/runs/E3/runtime/native_candidate_maps.f32').read_bytes()
 (T/f'expected_call_{call}.f32').write_bytes(data[int(r['offset_bytes']):int(r['offset_bytes'])+int(r['count'])*4])
 dump(T/f'replay_call_{call}.json',{'candidate':r,'rng':next(x for x in rng if x['call']==call)})
scene={'nx':nx,'ny':ny,'origin':[nav['origin_x'],nav['origin_y']],'cell_size':cell,'occupancy':occ.tolist(),'wind_xy':wind.tolist(),'logodds':logodds.tolist(),'confidence':confidence.tolist(),'params':P,'stops':stops,'input_scope':'Exact final native posterior snapshot contains the float wind grid used by source update4. Replay589/660 must match full native maps, scores and RNG endpoints before any mechanism arms.'}
dump(T/'scene.json',scene)

# Precommit without inspecting any new simulation result.
prng=np.random.Generator(np.random.PCG64(2026102411))
start=np.array([nav['origin_x']+6*cell,nav['origin_y']+14*cell]);end=start+np.array([5,4])*cell
fixedB=prng.uniform(start,end,size=(4,2)).tolist()
for pt in fixedB:
 c=int((pt[0]-nav['origin_x'])/cell);r=int((pt[1]-nav['origin_y'])/cell);assert occ[c+r*nx]==0
plan={'identity':'V11_E3_FUNCTION4ARMS_16_V1','status':'PREREGISTERED_BEFORE_NEW_FORWARD_OUTPUT','arms':{'A':'native per-filament uniform source over the frozen5x4region','B':'one precommitted uniformly sampled region point per full scenario','C':'fixed exact true point, offline mechanism diagnostic only','D':'fixed previously locked wrong MAP point'},'replicate_uniform_seeds':[11001,11002,11003,11004],'B_fixed_points':fixedB,'C_fixed_point':[-4.0,-1.9],'D_fixed_point':[-2.375,-4.875],'full_mechanism_simulations':16,'mandatory_original_replay_calls':[589,660],'event':'native at-least-one-puff-center-in-cell-per-record-step','record_steps':200,'max_warmup':500,'noiseSTDev':0.5,'deltaTime':0.1,'full_truth_wind':False,'neural_training':0,'ROS_goals':0,'new_GADEN_worlds':0,'per_process_wall_cap_s':120,'full_stage_wall_cap_s':300,'new_output_cap_bytes':16777216,'RNG_scope':'Four predetermined distinct uniform initial states and the original default-normal2500entry native cache. No claim of fully independent Gaussian trajectories. Same cache initialization semantics; record all state endpoints.','normal_stop_m2':1.0,'scientific_scope':'Fixed-history transport diagnostics, not a new posterior map/closedloop/localization gain','input_SHA256':{'scene.json':sha((T/'scene.json').read_bytes())}}
dump(T/'PREREGISTERED_16.json',plan)

sim=(S/'src/gsl_server/algorithms/PMFS/internal/Simulations.cpp').read_text(encoding='utf-8')
lib=(S/'src/gsl_server/algorithms/PMFS/PMFSLib.cpp').read_text(encoding='utf-8')
def extract(text,needle):
 a=text.index(needle);b=text.index('{',a);depth=0
 for e in range(b,len(text)):
  depth+=(text[e]=='{')-(text[e]=='}')
  if depth==0:return text[a:e+1]
 raise AssertionError(needle)
functions=[]
for signature in ['double Simulations::sourceProbFromMaps','void Simulations::moveFilament','bool Simulations::filamentIsOutside','void Simulations::simulateSourceInPosition','Vector2 SimulationSource::getPoint','bool Simulations::moveAlongPath']:
 functions.append({'signature':signature,'text':extract(sim,signature)})
pathfn=extract(lib,'bool PMFSLib::pathFree')
dump(T/'VERBATIM_FUNCTIONS.json',[{'signature':x['signature'],'sha256':sha(x['text'].encode())} for x in functions]+[{'signature':'bool PMFSLib::pathFree','sha256':sha(pathfn.encode())}])
stubs=T/'compatibility_headers'
for rel,content in {
 'geometry_msgs/msg/pose_with_covariance_stamped.hpp':'#pragma once\nnamespace geometry_msgs::msg {struct Pose { struct XYZ {double x=0,y=0,z=0;} position; };}\n',
 'gsl_server/core/Logging.hpp':'#pragma once\n#define GSL_ERROR(...) throw std::runtime_error("visibility capacity error")\n#define GSL_ASSERT(x) assert(x)\n',
 'gsl_server/algorithms/PMFS/internal/Settings.hpp':'#pragma once\nnamespace GSL::PMFS_internal { struct SimulationSettings { bool useWindGroundTruth;int maxRegionSize,stepsBetweenSourceUpdates;double sourceDiscriminationPower,refineFraction;int maxWarmupIterations,iterationsToRecord;double deltaTime,noiseSTDev; }; }\n',
}.items():
 p=stubs/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8')

head=r'''#include <bits/stdc++.h>
#include <nlohmann/json.hpp>
#include <DDA/DDA.h>
#include <xxHash/xxhash32.h>
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <gsl_server/algorithms/Common/Utils/Profiling.hpp>
using json=nlohmann::json;
namespace Audit {
uint32_t seed,state;uint64_t uc,uh,gc,gh;int ix;std::array<float,2500> table;
uint64_t hstep(uint64_t h,uint64_t x){return(h^x)*1099511628211ULL;}
void loadTable(const std::string&p){std::ifstream f(p,std::ios::binary);f.read(reinterpret_cast<char*>(table.data()),10000);if(f.gcount()!=10000)throw std::runtime_error("cache read failed");}
void restore(const json&b){seed=b.at("seed");state=b.at("state");uc=b.at("uc");uh=b.at("uh");gc=b.at("gc");gh=b.at("gh");ix=b.at("index");}
json end(){return {{"seed",seed},{"state",state},{"uc",uc},{"uh",uh},{"gc",gc},{"gh",gh},{"index",ix}};}
struct RestoredCache {float nextValue(float mean,float stdev){ix=(ix+1)%2500;uint32_t b;std::memcpy(&b,&table[ix],4);gc++;gh=hstep(gh,b);return mean+stdev*table[ix];}};
}
namespace GSL::Utils {
double uniformRandom(double min,double max){Audit::state=XXHash32::hash(&Audit::state,sizeof(Audit::state),Audit::seed);++Audit::uc;Audit::uh=Audit::hstep(Audit::uh,Audit::state);constexpr double reciprocalMax=1/(double)std::numeric_limits<uint32_t>::max();double rndVal01=Audit::state*reciprocalMax;return min+rndVal01*(max-min);}
double lerp(double a,double b,double p){if(p<0||std::isnan(p))return a;return a+(b-a)*std::min(1.,p);}
double logOddsToProbability(double x){return 1.-1./(1+std::exp(x));}
}
namespace GSL {struct PMFSLib {static bool pathFree(Grid2DMetadata,const std::vector<Occupancy>&,const Vector2&,const Vector2&);};
'''
tail=r'''
}
namespace GSL::PMFS_internal {
static Audit::RestoredCache gaussian;
'''
body='\n\n'.join(f['text'] for f in functions)
main=r'''
}
struct Probe: GSL::PMFS_internal::Simulations {using Simulations::Simulations;using Simulations::simulateSourceInPosition;using Simulations::sourceProbFromMaps;};
json readj(const std::string&p){std::ifstream f(p);json j;f>>j;return j;}
int main(int argc,char**argv){
 try {
  if(argc!=6)throw std::runtime_error("runner scene mode spec outprefix cache");
  auto j=readj(argv[1]);std::string mode=argv[2];auto spec=readj(argv[3]);std::string out=argv[4];Audit::loadTable(argv[5]);
  using namespace GSL;using namespace GSL::PMFS_internal;
  Grid2DMetadata md;md.dimensions={j["nx"],j["ny"]};md.origin={j["origin"][0],j["origin"][1]};md.cellSize=j["cell_size"];md.scale=25;
  size_t n=md.dimensions.x*md.dimensions.y;std::vector<Occupancy>occ(n);std::vector<HitProbability>hit(n);std::vector<double>prior(n);std::vector<Vector2>wind(n);
  for(size_t i=0;i<n;i++){occ[i]=j["occupancy"][i]==0?Occupancy::Free:Occupancy::Obstacle;hit[i].logOdds=j["logodds"][i];hit[i].confidence=j["confidence"][i];wind[i]={j["wind_xy"][i][0],j["wind_xy"][i][1]};}
  Grid2D<HitProbability>hg(hit,occ,md);Grid2D<double>pg(prior,occ,md);Grid2D<Vector2>wg(wind,occ,md);
  SimulationSettings s{};s.sourceDiscriminationPower=j["params"]["sourceDiscriminationPower"];s.maxWarmupIterations=j["params"]["maxWarmupIterations"];s.iterationsToRecord=j["params"]["iterationsToRecord"];s.deltaTime=j["params"]["deltaTime"];s.noiseSTDev=j["params"]["noiseSTDev"];
  Probe probe(hg,pg,wg,s);VisibilityMap visibility(md.dimensions.y,md.dimensions.x,5);
  for(int x=0;x<md.dimensions.x;x++)for(int y=0;y<md.dimensions.y;y++){
   std::vector<Vector2Int>v;if(hg.freeAt(x,y)){
    int oi=std::max(0,x-5)-x,fi=std::min(md.dimensions.x-1,x+5)-x,oj=std::max(0,y-5)-y,fj=std::min(md.dimensions.y-1,y+5)-y;
    for(int dx=oi;dx<=fi;dx++)for(int dy=oj;dy<=fj;dy++){Vector2Int to(x+dx,y+dy);if(to==Vector2Int(x,y)||PMFSLib::pathFree(md,occ,md.indexToCoordinates(x,y),md.indexToCoordinates(to)))v.push_back(to);}
   }visibility.emplace({x,y},v);
  }probe.visibilityMap=&visibility;
  std::vector<std::vector<uint8_t>> qmap(md.dimensions.x,std::vector<uint8_t>(md.dimensions.y));for(int x=0;x<md.dimensions.x;x++)for(int y=0;y<md.dimensions.y;y++)qmap[x][y]=hg.freeAt(x,y)?1:0;
  int ox=6,oy=14,sx=5,sy=4;if(mode=="replay"){auto c=spec["candidate"];ox=std::stoi(c["origin_x"].get<std::string>());oy=std::stoi(c["origin_y"].get<std::string>());sx=std::stoi(c["size_x"].get<std::string>());sy=std::stoi(c["size_y"].get<std::string>());Audit::restore(spec["rng"]["before"]);}
  else {Audit::seed=spec["seed"];Audit::state=65535;Audit::uc=Audit::gc=0;Audit::uh=Audit::gh=1469598103934665603ULL;Audit::ix=Utils::uniformRandom(0,2500);}
  Utils::NQA::Node region(nullptr,{ox,oy},{sx,sy},qmap);Vector2 pt(0,0);if(mode!="replay"&&spec["arm"]!="A")pt={spec["point"][0],spec["point"][1]};
  SimulationSource src=(mode=="replay"||spec["arm"]=="A")?SimulationSource(&region,md):SimulationSource(pt,md);
  auto before=Audit::end();std::vector<float>freq(n,0.0f);auto t0=std::chrono::steady_clock::now();
  probe.simulateSourceInPosition(src,freq,true,s.maxWarmupIterations,s.iterationsToRecord,s.deltaTime,s.noiseSTDev);
  auto after=Audit::end();double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
  json stops=json::array();for(auto q:j["stops"]){int k=q["cell"][0].get<int>()+q["cell"][1].get<int>()*md.dimensions.x;q["prediction"]=freq[k];stops.push_back(q);}
  double score=probe.sourceProbFromMaps(hg,freq);std::ofstream f(out+".f32",std::ios::binary);f.write(reinterpret_cast<const char*>(freq.data()),freq.size()*4);f.close();
  json result={{"mode",mode},{"spec",spec},{"score",score},{"before",before},{"after",after},{"simulation_wall_s",seconds},{"filament_moves",(after["gc"].get<uint64_t>()-before["gc"].get<uint64_t>())/2},{"stops",stops}};std::ofstream o(out+".json");o<<std::setw(2)<<result<<"\n";
  std::cout<<json({{"status","DONE_FUNCTION_CALL"},{"mode",mode},{"score",score},{"seconds",seconds}})<<"\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}
}
'''
(T/'native_function_runner.cpp').write_text(head+pathfn+tail+body+main,encoding='utf-8')
dump(T/'FUNCTION_EXTRACTION_IDENTITY.json',{'frozen_source_root':str(S),'simulation_file_sha256':sha((S/'src/gsl_server/algorithms/PMFS/internal/Simulations.cpp').read_bytes()),'cpp_sha256':sha((T/'native_function_runner.cpp').read_bytes()),'transport_and_score_functions':'Extracted verbatim; native DDA/vector/grid/visibility headers; standalone ROS-message/logging/settings declarations only; replayable RNG adapter replaces initialization with recorded state/cache.','frozen_baseline_edited':False,'gate':'All2112floats plus native score and RNG counters/endpoints must reproduce both calls589and660 before16arms.'})
print(json.dumps({'status':'PREPARED_AND_PREREGISTERED','trial':str(T),'B_points':fixedB,'nx':nx,'ny':ny,'stops':len(stops)},ensure_ascii=False))
