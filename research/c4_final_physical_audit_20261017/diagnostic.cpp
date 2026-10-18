#include "support.hpp"
#include <zlib.h>
using namespace GSL; using namespace GSL::PMFS_internal; namespace fs=std::filesystem;
using Row=std::map<std::string,std::string>;
std::vector<std::string> split(const std::string&s){std::vector<std::string>a;size_t b=0;while(true){auto e=s.find(',',b);a.push_back(s.substr(b,e==std::string::npos?e:e-b));if(e==std::string::npos)break;b=e+1;}return a;}
std::vector<Row> csv(const fs::path&p){std::ifstream f(p);if(!f)throw std::runtime_error("Missing "+p.string());std::string s;std::getline(f,s);if(!s.empty()&&s.back()=='\r')s.pop_back();auto h=split(s);std::vector<Row>a;while(std::getline(f,s)){if(!s.empty()&&s.back()=='\r')s.pop_back();if(s.empty())continue;auto v=split(s);if(v.size()!=h.size())throw std::runtime_error("CSV shape "+p.string());Row r;for(size_t i=0;i<h.size();i++)r[h[i]]=v[i];a.push_back(r);}return a;}
int integer(const Row&r,const char*k){return std::stoi(r.at(k));}double d(const Row&r,const char*k){return std::stod(r.at(k));}
template<class T>void binary(const fs::path&p,const std::vector<T>&a){std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(a.data()),a.size()*sizeof(T));if(!f)throw std::runtime_error("Output failed "+p.string());}
struct Tagged { Filament f; uint64_t seen=0; size_t last=size_t(-1); };
struct Result { int warmup=0; uint64_t emitted=0,exited=0; size_t warm_survivors=0,final_survivors=0; int first_exit=-1,first_exit_phase=-1; };

// Identical native release/movement/mark/remove order. Tags, gzip diagnostics
// and map snapshots do not consume random numbers or modify a physical state.
Result timed(const Simulations&sim,const SimulationSource&source,std::vector<float>&map,
             int W,int T,const std::vector<int>&receivers,const fs::path&dest) {
 const auto&settings=sim.settings; const float dt=settings.deltaTime,noise=settings.noiseSTDev;
 std::vector<Tagged>a,b;size_t cap=5*(std::max(W,settings.maxWarmupIterations)+T);
 a.reserve(cap);b.reserve(cap);auto*active=&a;auto*other=&b;
 std::vector<uint16_t>updated(map.size(),0); std::vector<float>previous(map.size(),0.f);
 Result result; bool stable=false; int warm=0;
 gzFile trace=gzopen((dest/"trace.u32.gz").c_str(),"wb6");if(!trace)throw std::runtime_error("Trace open failed");
 std::vector<uint32_t>record(9+3*receivers.size());
 auto step=[&](int phase,int t,float delta){
  for(int i=0;i<5;i++){active->emplace_back();active->back().f.position=source.getPoint();++result.emitted;}
  std::fill(record.begin(),record.end(),0);record[0]=phase;record[1]=t;record[2]=active->size();
  for(auto &tag:*active){
   auto idx=sim.measuredHitProb.metadata.coordinatesToIndices(tag.f.position.x,tag.f.position.y);
   GSL_ASSERT(sim.measuredHitProb.metadata.indicesInBounds(idx));
   size_t index=sim.measuredHitProb.metadata.indexOf(idx);
   if(phase==1&&updated[index]<t){map[index]++;updated[index]=t;}
   for(size_t r=0;r<receivers.size();r++)if(index==size_t(receivers[r])){
    ++record[9+3*r];uint64_t bit=uint64_t(1)<<r;
    if(!(tag.seen&bit)){tag.seen|=bit;++record[10+3*r];}
    if(tag.last!=index)++record[11+3*r];
   }
   tag.last=index;
   sim.moveFilament(tag.f,idx,delta,noise);
   if(sim.filamentIsOutside(tag.f)){stable=true;++result.exited;++record[4];if(result.first_exit<0){result.first_exit=t;result.first_exit_phase=phase;}}
   else other->push_back(tag);
  }
  record[3]=other->size();record[5]=uint32_t(result.emitted);record[6]=uint32_t(result.exited);
  record[7]=uint32_t(diag::moves);record[8]=uint32_t(diag::moves>>32);
  if(gzwrite(trace,record.data(),record.size()*sizeof(uint32_t))!=int(record.size()*sizeof(uint32_t)))throw std::runtime_error("Trace write failed");
  active->clear();std::swap(active,other);
 };
 while(W>=0 ? warm<W : warm<settings.minWarmupIterations || (!stable&&warm<settings.maxWarmupIterations)){
  step(0,warm+1,dt*2);++warm;
 }
 result.warmup=warm;result.warm_survivors=active->size();
 auto snapshot=[&](const std::string&name,std::vector<float>values,int denom){
  for(size_t k=0;k<values.size();k++)if(sim.measuredHitProb.occupancy[k]==Occupancy::Free)values[k]/=denom;
  binary(dest/(name+"_raw.f32"),values);cv::Mat img(values);img=img.reshape(1,sim.measuredHitProb.metadata.dimensions.y);sim.blurHitMap(img);binary(dest/(name+"_blur.f32"),values);
 };
 for(int t=1;t<T+1;t++){
  step(1,t,dt);
  if(t%100==0||t==T){
   std::vector<float>block(map.size());for(size_t k=0;k<map.size();k++)block[k]=map[k]-previous[k];
   snapshot("block_"+std::to_string(t),block,t%100?t%100:100);previous=map;
  }
  if(t%200==0||t==T)snapshot("cumulative_"+std::to_string(t),map,t);
 }
 result.final_survivors=active->size();if(gzclose(trace)!=Z_OK)throw std::runtime_error("Trace close failed");
 for(size_t k=0;k<map.size();k++)if(sim.measuredHitProb.occupancy[k]==Occupancy::Free)map[k]/=T;
 return result;
}

int main(int argc,char**argv){try{
 if(argc!=7)throw std::runtime_error("timed FIXTURE JOBS OUTPUT STATE WARMUP_STEPS RECORD_STEPS");
 fs::path fixture=argv[1],jobsfile=argv[2],out=argv[3];int seed=std::stoi(argv[4]),W=std::stoi(argv[5]),T=std::stoi(argv[6]);
 if(fs::exists(out))throw std::runtime_error("Refusing overwrite");fs::create_directories(out);
 auto mr=csv(fixture/"metadata.csv").at(0);auto data=csv(fixture/"input.csv");
 Grid2DMetadata m;m.dimensions={integer(mr,"width"),integer(mr,"height")};m.origin={float(d(mr,"origin_x")),float(d(mr,"origin_y"))};m.cellSize=d(mr,"cell_size");m.scale=25;m.numFreeCells=integer(mr,"free_cells");
 size_t count=m.dimensions.x*m.dimensions.y;GSL_ASSERT(data.size()==count);
 std::vector<Occupancy>occ(count);std::vector<HitProbability>hp(count);std::vector<Vector2>wind(count);
 for(size_t k=0;k<count;k++){GSL_ASSERT(integer(data[k],"cell_index")==k);occ[k]=integer(data[k],"occupancy")==1?Occupancy::Free:Occupancy::Obstacle;hp[k].logOdds=d(data[k],"logOdds");hp[k].confidence=d(data[k],"confidence");hp[k].omega=d(data[k],"omega");wind[k]={float(d(data[k],"u")),float(d(data[k],"v"))};}
 auto sr=csv(fixture/"settings.csv").at(0);SimulationSettings settings;
 settings.deltaTime=d(sr,"deltaTime");settings.noiseSTDev=d(sr,"noiseSTDev");settings.iterationsToRecord=integer(sr,"iterationsToRecord");settings.minWarmupIterations=integer(sr,"minWarmupIterations");settings.maxWarmupIterations=integer(sr,"maxWarmupIterations");settings.blurSigmaX=d(sr,"blurSigmaX");settings.blurSigmaY=d(sr,"blurSigmaY");settings.sourceDiscriminationPower=d(sr,"sourceDiscriminationPower");
 Simulations sim(settings,Grid2D<HitProbability>(hp,occ,m),Grid2D<Vector2>(wind,occ,m));
 VisibilityMap visibility(m.dimensions.x,m.dimensions.y,5);sim.visibilityMap=&visibility;sim.freeSpaceMask=cv::Mat(cv::Size(m.dimensions.x,m.dimensions.y),CV_32F,cv::Scalar(0));
 for(int y=0;y<m.dimensions.y;y++)for(int x=0;x<m.dimensions.x;x++){Vector2Int ij(x,y);std::vector<Vector2Int>v;if(occ[m.indexOf(ij)]==Occupancy::Free){sim.freeSpaceMask.at<float>(y,x)=1;for(int j=std::max(0,y-5);j<=std::min(m.dimensions.y-1,y+5);j++)for(int i=std::max(0,x-5);i<=std::min(m.dimensions.x-1,x+5);i++){Vector2Int z(i,j);if(z==ij||GridUtils::PathFree(m,occ,m.indicesToCoordinates(ij),m.indicesToCoordinates(z)))v.push_back(z);}}visibility.emplace(ij,v);}
 auto rxs=csv(fixture/"receivers.csv");std::vector<int>receivers;
 for(auto&r:rxs){int k=integer(r,"cell_index");GSL_ASSERT(k>=0&&k<count&&occ[k]==Occupancy::Free);receivers.push_back(k);}
 GSL_ASSERT(receivers.size()<64);
 std::ofstream scores(out/"scores.csv");scores<<std::setprecision(21)<<"job_id,seed,warmup_steps,record_steps,source_logscore,source_score,emitted,exited,warm_survivors,final_survivors,first_exit_step,first_exit_phase,particle_moves,cpu_s,wall_s,rng_before,rng_after,gaussian_before,gaussian_after\n";
 int n=0;
 for(auto&r:csv(jobsfile))if(r.at("key")==fixture.filename().string()&&integer(r,"seed")==seed){
  std::string id=r.at("job_id");fs::path dest=out/id;fs::create_directories(dest);
  std::array<float,2500>cache;std::ifstream cf(fixture/("cache_"+r.at("mode")+"_"+r.at("seed")+".f32"),std::ios::binary);cf.read(reinterpret_cast<char*>(cache.data()),sizeof(cache));GSL_ASSERT(bool(cf));
  // Initialize original TLS constructor before restoration, then restore both states.
  gaussian.restore(cache,integer(r,"gaussian_before"));Utils::restore_rng(r.at("rng_before"));
  diag::replay=false;diag::moves=0;diag::releases=0;
  Utils::NQA::Node node{{integer(r,"origin_i"),integer(r,"origin_j")},{integer(r,"size_i"),integer(r,"size_j")}};
  SimulationSource source=r.at("mode")=="oracle"?SimulationSource(Vector2(float(d(r,"point_x")),float(d(r,"point_y"))),m):SimulationSource(&node,m);
  std::vector<float>map(count,0.f);auto start=std::chrono::steady_clock::now();auto cpu=std::clock();
  auto result=timed(sim,source,map,W,T,receivers,dest);
  binary(dest/"raw.f32",map);cv::Mat img(map);img=img.reshape(1,m.dimensions.y);sim.blurHitMap(img);binary(dest/"blur.f32",map);long double score=sim.sourceProbFromMaps(sim.measuredHitProb,map);
  scores<<id<<","<<seed<<","<<result.warmup<<","<<T<<","<<std::log(score)<<","<<score<<","<<result.emitted<<","<<result.exited<<","<<result.warm_survivors<<","<<result.final_survivors<<","<<result.first_exit<<","<<result.first_exit_phase<<","<<diag::moves<<","<<double(std::clock()-cpu)/CLOCKS_PER_SEC<<","<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<","<<r.at("rng_before")<<","<<Utils::rng_state()<<","<<r.at("gaussian_before")<<","<<gaussian.index()<<"\n";scores.flush();++n;
 }
 std::ofstream(out/"COMPLETE.json")<<"{\"simulations\":"<<n<<",\"seed\":"<<seed<<",\"warmup_requested_steps\":"<<W<<",\"record_steps\":"<<T<<"}";
 std::cout<<"COMPLETE "<<fixture.filename()<<" "<<seed<<" "<<W<<" "<<T<<" jobs="<<n<<std::endl;
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
