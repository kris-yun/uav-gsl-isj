#include "support.hpp"
using namespace GSL;using namespace GSL::PMFS_internal;namespace fs=std::filesystem;
using Row=std::map<std::string,std::string>;
std::vector<std::string> split(const std::string&s){std::vector<std::string>a;size_t b=0;while(true){auto e=s.find(',',b);a.push_back(s.substr(b,e==std::string::npos?e:e-b));if(e==std::string::npos)break;b=e+1;}return a;}
std::vector<Row> csv(const fs::path&p){std::ifstream f(p);if(!f)throw std::runtime_error("Missing "+p.string());std::string s;std::getline(f,s);if(s.back()=='\r')s.pop_back();auto h=split(s);std::vector<Row>a;while(std::getline(f,s)){if(!s.empty()&&s.back()=='\r')s.pop_back();if(s.empty())continue;auto v=split(s);if(v.size()!=h.size())throw std::runtime_error("CSV shape");Row r;for(size_t i=0;i<h.size();i++)r[h[i]]=v[i];a.push_back(r);}return a;}
int integer(const Row&r,const char*k){return std::stoi(r.at(k));}double d(const Row&r,const char*k){return std::stod(r.at(k));}
template<class T>void binary(const fs::path&p,const std::vector<T>&a){std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(a.data()),a.size()*sizeof(T));if(!f)throw std::runtime_error("Output write failed");}
int main(int argc,char**argv){try{
 if(argc!=7)throw std::runtime_error("forward MODE FIXTURE NATIVE_UPDATE OUTPUT SEED TAG");
 std::string mode=argv[1],tag=argv[6];fs::path fixture=argv[2],native=argv[3],out=argv[4];unsigned long seed=std::stoul(argv[5]);
 if(fs::exists(out))throw std::runtime_error("Refusing to overwrite output");fs::create_directories(out/"maps");
 auto mr=csv(fixture/"metadata.csv").at(0),input=Row{};auto data=csv(native/"input.csv");
 Grid2DMetadata m;m.dimensions={integer(mr,"width"),integer(mr,"height")};m.origin={float(d(mr,"origin_x")),float(d(mr,"origin_y"))};m.cellSize=d(mr,"cell_size");m.scale=25;m.numFreeCells=integer(mr,"free_cells");
 const size_t count=m.dimensions.x*m.dimensions.y;if(data.size()!=count)throw std::runtime_error("Input dimensions");
 std::vector<Occupancy>occ(count);std::vector<HitProbability>hp(count);std::vector<Vector2>wind(count);
 for(size_t k=0;k<count;k++){if(integer(data[k],"cell_index")!=k)throw std::runtime_error("Input order");occ[k]=integer(data[k],"occupancy")==1?Occupancy::Free:Occupancy::Obstacle;hp[k].logOdds=d(data[k],"logOdds");hp[k].confidence=d(data[k],"confidence");hp[k].omega=d(data[k],"omega");wind[k]={float(d(data[k],"u")),float(d(data[k],"v"))};}
 auto sr=csv(fixture/"settings.csv").at(0);SimulationSettings settings;
 settings.deltaTime=d(sr,"deltaTime");settings.noiseSTDev=d(sr,"noiseSTDev");settings.iterationsToRecord=integer(sr,"iterationsToRecord");settings.minWarmupIterations=integer(sr,"minWarmupIterations");settings.maxWarmupIterations=integer(sr,"maxWarmupIterations");settings.blurSigmaX=d(sr,"blurSigmaX");settings.blurSigmaY=d(sr,"blurSigmaY");settings.sourceDiscriminationPower=d(sr,"sourceDiscriminationPower");
 Simulations sim(settings,Grid2D<HitProbability>(hp,occ,m),Grid2D<Vector2>(wind,occ,m));
 VisibilityMap visibility(m.dimensions.x,m.dimensions.y,5);sim.visibilityMap=&visibility;sim.freeSpaceMask=cv::Mat(cv::Size(m.dimensions.x,m.dimensions.y),CV_32F,cv::Scalar(0));
 for(int y=0;y<m.dimensions.y;y++)for(int x=0;x<m.dimensions.x;x++){Vector2Int ij(x,y);std::vector<Vector2Int>v;if(occ[m.indexOf(ij)]==Occupancy::Free){sim.freeSpaceMask.at<float>(y,x)=1;for(int j=std::max(0,y-5);j<=std::min(m.dimensions.y-1,y+5);j++)for(int i=std::max(0,x-5);i<=std::min(m.dimensions.x-1,x+5);i++){Vector2Int z(i,j);if(z==ij||GridUtils::PathFree(m,occ,m.indicesToCoordinates(ij),m.indicesToCoordinates(z)))v.push_back(z);}}visibility.emplace(ij,v);}
 auto candidates=csv(native/"candidates.csv"),initial=csv(native/"gaussian_initial.csv");
 std::array<float,2500>cache;std::ifstream cf(native/"gaussian_cache.f32",std::ios::binary);cf.read(reinterpret_cast<char*>(cache.data()),sizeof(cache));if(!cf)throw std::runtime_error("Gaussian cache missing");
 // Touch TLS before setting a new prediction state. Its original constructor is retained.
 gaussian.restore(cache,0);
 if(mode!="parity") {Utils::restore_rng(std::to_string(seed));uint16_t index=Utils::uniformRandom(0,2500);for(float&v:cache)v=Utils::randomFromGaussian(0,1);gaussian.restore(cache,index);}
 binary(out/"gaussian_cache.f32",std::vector<float>(cache.begin(),cache.end()));
 std::vector<Row>jobs;std::vector<Row>leaves;
 for(const auto&r:csv(native/"final_tree.csv"))if(integer(r,"value")==1&&!integer(r,"has_children"))leaves.push_back(r);
 std::vector<int>owner(count,-1);
 for(size_t a=0;a<leaves.size();a++){auto&r=leaves[a];for(int y=integer(r,"origin_j");y<integer(r,"origin_j")+integer(r,"size_j");y++)for(int x=integer(r,"origin_i");x<integer(r,"origin_i")+integer(r,"size_i");x++){auto k=m.indexOf(x,y);if(k>=count||occ[k]!=Occupancy::Free||owner[k]!=-1)throw std::runtime_error("Invalid source partition");owner[k]=a;}}
 for(size_t k=0;k<count;k++)if((owner[k]>=0)!=(occ[k]==Occupancy::Free))throw std::runtime_error("Incomplete source support");
 if(mode=="parity"){jobs=candidates;}
 else if(mode=="region"){for(auto r:leaves){r["candidate_id"]=r.at("node_id");r["parent_id"]=r.at("node_id");jobs.push_back(r);}}
 else if(mode=="coarse_equal"||mode=="fine"){for(size_t k=0;k<count;k++)if(owner[k]>=0){Row r=leaves[owner[k]];r["candidate_id"]="cell_"+std::to_string(k);r["parent_id"]=r.at("node_id");if(mode=="fine"){r["origin_i"]=std::to_string(k%m.dimensions.x);r["origin_j"]=std::to_string(k/m.dimensions.x);r["size_i"]="1";r["size_j"]="1";}jobs.push_back(r);}}
 else throw std::runtime_error("Unknown mode");
 std::ofstream scores(out/"scores.csv");scores<<std::setprecision(21)<<"id,parent_id,origin_i,origin_j,size_i,size_j,score,logscore,releases,particle_moves,cpu_s,wall_s,rng_before,rng_after,gaussian_before,gaussian_after\n";
 size_t number=0;for(const auto&r:jobs){
  if(mode=="parity"){size_t np=std::stoul(r.at("point_count"));std::vector<float>v(np*2);std::ifstream f(native/r.at("points_file"),std::ios::binary);f.read(reinterpret_cast<char*>(v.data()),v.size()*sizeof(float));if(!f)throw std::runtime_error("Archived source positions missing");diag::points.clear();for(size_t k=0;k<np;k++)diag::points.emplace_back(v[2*k],v[2*k+1]);diag::offset=0;diag::replay=true;gaussian.restore(cache,integer(r,"gaussian_ready_before")?integer(r,"gaussian_index_before"):integer(initial.at(0),"index"));Utils::restore_rng(r.at("rng_before"));}
  else diag::replay=false;
  std::string rng_before=Utils::rng_state();auto gi=gaussian.index();diag::moves=0;diag::releases=0;
  auto start=std::chrono::steady_clock::now();auto cpu=std::clock();
  Utils::NQA::Node node{{integer(r,"origin_i"),integer(r,"origin_j")},{integer(r,"size_i"),integer(r,"size_j")}};SimulationSource source(&node,m);std::vector<float>map(count,0.f);
  sim.simulateSourceInPosition(source,map,true,settings.iterationsToRecord,settings.deltaTime,settings.noiseSTDev);
  auto id=r.at("candidate_id");binary(out/"maps"/(id+"_unblurred.f32"),map);cv::Mat img(map);img=img.reshape(1,m.dimensions.y);sim.blurHitMap(img);
  long double score=sim.sourceProbFromMaps(sim.measuredHitProb,map);binary(out/"maps"/(id+".f32"),map);
  if(mode=="parity"&&(diag::offset!=std::stoul(r.at("point_count"))||gaussian.index()!=integer(r,"gaussian_index_after")))throw std::runtime_error("Archived RNG consumption mismatch "+id);
  scores<<id<<","<<(r.count("parent_id")?r.at("parent_id"):id)<<","<<node.origin.x<<","<<node.origin.y<<","<<node.size.x<<","<<node.size.y<<","<<score<<","<<std::log(score)<<","<<diag::releases<<","<<diag::moves<<","<<double(std::clock()-cpu)/CLOCKS_PER_SEC<<","<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<","<<rng_before<<","<<Utils::rng_state()<<","<<gi<<","<<gaussian.index()<<"\n";scores.flush();
  if(++number%100==0)std::cout<<tag<<" "<<number<<"/"<<jobs.size()<<std::endl;
 }
 std::ofstream(out/"COMPLETE.json")<<"{\"simulations\":"<<jobs.size()<<",\"seed\":"<<seed<<",\"new_worlds\":0,\"new_ROS_episodes\":0}";
 std::cout<<"COMPLETE "<<tag<<" "<<jobs.size()<<std::endl;return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
