// Isolated, source-blind, frozen observation/operator replay. No ROS init or navigation.
#include "Fixture.hpp"
#include <omp.h>
#include <cerrno>
#include <cstdlib>
#include <opencv2/imgproc.hpp>
namespace GSL::PMFS_internal {
void r4_set_gaussian(const std::array<float,2500>&,uint16_t);
uint16_t r4_gaussian_index();
}
using namespace R4;
double number(const Row& r,const char* k) {
 const std::string& s=r.at(k);char* end=nullptr;errno=0;double x=std::strtod(s.c_str(),&end);
 if(end==s.c_str()||*end||!std::isfinite(x))throw std::runtime_error(std::string("invalid finite ")+k);return x;
}
class NativeEntry:public Simulations {
public:using Simulations::Simulations;
 long double supplied(const std::vector<float>& q){return sourceProbFromMaps(measuredHitProb,q);}
 long double forward(const Utils::NQA::Node& node,bool exact=false,Vector2 point={0,0}) {
  std::vector<float> q(measuredHitProb.data.size(),0.f);R4Audit::begin(&node);
  SimulationSource src=exact?SimulationSource(point,measuredHitProb.metadata):SimulationSource(&node,measuredHitProb.metadata);
  simulateSourceInPosition(src,q,true,settings.iterationsToRecord,settings.deltaTime,settings.noiseSTDev);
  R4Audit::before_blur(&node,q);
  if(settings.blurSigmaX>0||settings.blurSigmaY>0){cv::Mat im(q);im=im.reshape(1,measuredHitProb.metadata.dimensions.y);blurHitMap(im);}
  long double score=sourceProbFromMaps(measuredHitProb,q);R4Audit::end(&node,q,score,r4_gaussian_index());return score;
 }
 void blur(std::vector<float>& q,const fs::path& out){
  cv::Mat raw(q);raw=raw.reshape(1,measuredHitProb.metadata.dimensions.y);
  cv::Mat num,den;cv::GaussianBlur(raw,num,cv::Size(0,0),settings.blurSigmaX,settings.blurSigmaY);
  cv::GaussianBlur(freeSpaceMask,den,cv::Size(0,0),settings.blurSigmaX,settings.blurSigmaY);
  std::vector<float> before(q.size());int above=0,below=0;
  for(int y=0;y<num.rows;y++)for(int x=0;x<num.cols;x++){
   float a=num.at<float>(y,x),d=den.at<float>(y,x);float b=d!=0?a/d:a;before[x+y*num.cols]=b;
   above+=b>1;below+=b<0;
  }
  R4Audit::binary(out/"preclamp.f32",before);
  std::ofstream(out/"PRECLAMP.json")<<"{\"above_one\":"<<above<<",\"below_zero\":"<<below<<"}";
  blurHitMap(raw);
 }
};
struct ReplayState {
 Grid2DMetadata m;std::vector<Occupancy> occ;std::vector<HitProbability> hit;
 std::vector<double> post;std::vector<Vector2> flow;std::unique_ptr<VisibilityMap> vis;
 HitProbabilitySettings hp;SimulationSettings ss;int initialMoves=2,steps=3;
 ReplayState(const fs::path& d){
  auto rows=csv(d/"input.csv"),meta=csv(d/"metadata.csv");auto r=meta.at(0);
  m.dimensions={integer(r,"width"),integer(r,"height")};m.origin={float(number(r,"origin_x")),float(number(r,"origin_y"))};
  m.cellSize=number(r,"cell_size");m.numFreeCells=integer(r,"free_cells");m.scale=25;
  size_t n=m.dimensions.x*m.dimensions.y;if(rows.size()!=n)throw std::runtime_error("grid size");
  occ.resize(n);hit.resize(n);post.resize(n);flow.resize(n);
  for(size_t i=0;i<n;i++){
   auto& a=rows[i];if(integer(a,"cell_index")!=i)throw std::runtime_error("grid order");
   occ[i]=integer(a,"occupancy")==1?Occupancy::Free:Occupancy::Obstacle;
   hit[i].logOdds=number(a,"logOdds");hit[i].omega=number(a,"omega");hit[i].confidence=number(a,"confidence");
   hit[i].auxWeight=-1;hit[i].originalPropagationDirection={0,0};
   flow[i]={float(number(a,"u")),float(number(a,"v"))};post[i]=number(a,"prior_posterior");
  }
  auto settings=csv(d/"settings.csv").at(0);
  ss.maxRegionSize=integer(settings,"maxRegionSize");ss.sourceDiscriminationPower=number(settings,"sourceDiscriminationPower");
  ss.refineFraction=number(settings,"refineFraction");ss.deltaTime=number(settings,"deltaTime");ss.noiseSTDev=number(settings,"noiseSTDev");
  ss.iterationsToRecord=integer(settings,"iterationsToRecord");ss.minWarmupIterations=integer(settings,"minWarmupIterations");
  ss.maxWarmupIterations=integer(settings,"maxWarmupIterations");ss.blurSigmaX=number(settings,"blurSigmaX");ss.blurSigmaY=number(settings,"blurSigmaY");
  hp.prior=.3;hp.kernelSigma=1.5;hp.kernelStretchConstant=1.5;hp.confidenceSigmaSpatial=1;hp.confidenceMeasurementWeight=1;
  hp.localEstimationWindowSize=2;hp.maxUpdatesPerStop=5;
  if(settings.count("initialExplorationMoves"))initialMoves=integer(settings,"initialExplorationMoves");
  if(settings.count("stepsSourceUpdate"))steps=integer(settings,"stepsSourceUpdate");
  vis=std::make_unique<VisibilityMap>(m.dimensions.x,m.dimensions.y,5);
  for(int x=0;x<m.dimensions.x;x++)for(int y=0;y<m.dimensions.y;y++){
   Vector2Int ij{x,y};std::vector<Vector2Int>a;
   if(occ[m.indexOf(ij)]==Occupancy::Free)for(int j=std::max(0,y-5);j<=std::min(m.dimensions.y-1,y+5);j++)
    for(int i=std::max(0,x-5);i<=std::min(m.dimensions.x-1,x+5);i++){
     Vector2Int z{i,j};if(z==ij||GridUtils::PathFree(m,occ,m.indicesToCoordinates(ij),m.indicesToCoordinates(z)))a.push_back(z);
    }
   vis->emplace(ij,a);
  }
 }
 auto grid(){return Grid2D<HitProbability>(hit,occ,m);}
 std::unique_ptr<NativeEntry> simulation(){
  auto p=std::make_unique<NativeEntry>(grid(),Grid2D<double>(post,occ,m),Grid2D<Vector2>(flow,occ,m),ss);
  std::vector<std::vector<uint8_t>> map(m.dimensions.x,std::vector<uint8_t>(m.dimensions.y));
  for(int x=0;x<m.dimensions.x;x++)for(int y=0;y<m.dimensions.y;y++)map[x][y]=occ[m.indexOf({x,y})]==Occupancy::Free;
  p->initializeMap(map);p->visibilityMap=vis.get();p->varianceOfHitProb.resize(hit.size());return p;
 }
 void mapdump(const fs::path& p){std::ofstream f(p);f<<std::setprecision(17)<<"cell_index,grid_i,grid_j,occupancy,logOdds,omega,confidence,probability,u,v,prior_posterior\n";
  for(size_t i=0;i<hit.size();i++)f<<i<<','<<i%m.dimensions.x<<','<<i/m.dimensions.x<<','<<int(occ[i])<<','<<hit[i].logOdds<<','<<hit[i].omega<<','<<hit[i].confidence<<','<<hit[i].probability()<<','<<flow[i].x<<','<<flow[i].y<<','<<post[i]<<'\n';}
};
void rng(const fs::path& d){
 std::array<float,2500>c;std::ifstream f(d/"gaussian_cache.f32",std::ios::binary);f.read((char*)c.data(),sizeof(c));if(!f)throw std::runtime_error("cache missing");
 auto r=csv(d/"rng.csv").at(0);r4_set_gaussian(c,integer(r,"phase"));Utils::r4_rng_restore(r.at("engine"));
}
int main(int argc,char**argv){try{
 if(argc!=5)throw std::runtime_error("MODE INPUT PAYLOAD NEW_OUTPUT");
 if(omp_get_max_threads()!=1)throw std::runtime_error("single thread");cv::setNumThreads(1);
 std::string mode=argv[1];fs::path in=argv[2],payload=argv[3],out=argv[4];if(fs::exists(out))throw std::runtime_error("existing output");fs::create_directories(out);
 ReplayState s(in);auto sim=s.simulation();
 if(mode=="score"||mode=="blur_score"){
  auto jobs=csv(payload);std::ofstream f(out/"scores.csv");f<<std::setprecision(21)<<"id,score,log_score\n";
  for(auto& j:jobs){std::vector<float>q(s.hit.size());std::ifstream b(j.at("path"),std::ios::binary);b.read((char*)q.data(),q.size()*sizeof(float));if(!b)throw std::runtime_error("map missing");
   if(mode=="blur_score"){fs::path dest=out/j.at("id");fs::create_directories(dest);sim->blur(q,dest);R4Audit::binary(dest/"blurred.f32",q);}
   long double score=sim->supplied(q);f<<j.at("id")<<','<<score<<','<<std::log(score)<<'\n';
  }
 }else if((mode=="anchor_forward"||mode=="point_forward")){
  rng(in);auto j=csv(payload).at(0);R4Audit::initialize(out/"forward");R4Audit::cache_ready=true;R4Audit::last_index=r4_gaussian_index();
  Utils::NQA::Node node(nullptr,{integer(j,"origin_i"),integer(j,"origin_j")},{integer(j,"size_i"),integer(j,"size_j")},sim->quadtree->map);
  auto score=sim->forward(node,mode=="point_forward",mode=="point_forward"?Vector2(float(number(j,"point_x")),float(number(j,"point_y"))):Vector2(0,0));R4Audit::finish(s.post);std::ofstream(out/"score.txt")<<std::setprecision(21)<<score;
 }else if(mode=="map"||mode=="history"){
  for(auto& h:s.hit){h=HitProbability{};h.auxWeight=-1;h.originalPropagationDirection={0,0};h.setProbability(s.hp.prior);}
  if(mode=="history")rng(in);
  auto events=csv(payload);int count=0,updates=0;bool success=false;
  std::ofstream ledger(out/"update_ledger.csv"),contrib(out/"event_cell_lineage.csv");
  ledger<<std::setprecision(17)<<"update,blocks,variance,mean_x,mean_y,top5_x,top5_y,official_rule_first_convergence,rng_after,gaussian_phase\n";
  contrib<<std::setprecision(17)<<"block,cell_index,logOdds_delta,omega_delta,confidence_after,probability_after\n";
  for(auto& e:events){auto ij=s.m.coordinatesToIndices(float(number(e,"x")),float(number(e,"y")));
   if(!s.m.indicesInBounds(ij)||s.occ[s.m.indexOf(ij)]!=Occupancy::Free)throw std::runtime_error("receptor not free");
   auto before=s.hit;auto g=s.grid();PMFSLib::EstimateHitProbabilities(g,*s.vis,s.hp,integer(e,"event_hit"),number(e,"wind_direction_to"),number(e,"wind_speed"),ij);
   for(size_t i=0;i<s.hit.size();i++)if(s.occ[i]==Occupancy::Free)contrib<<count<<','<<i<<','<<s.hit[i].logOdds-before[i].logOdds<<','<<s.hit[i].omega-before[i].omega<<','<<s.hit[i].confidence<<','<<s.hit[i].probability()<<'\n';
   count++;if(count%5==0)s.mapdump(out/("map_blocks_"+std::to_string(count)+".csv"));
   int stop=count/5-1;
   if(mode=="history"&&count%5==0&&stop>=s.initialMoves&&stop%s.steps==0){
    auto d=out/("update_"+std::to_string(updates));R4Audit::initialize(d);R4Audit::tree(sim->QTleaves,"coarse_tree.csv");
    s.mapdump(d/"input_full.csv");sim->updateSourceProbability(s.ss.refineFraction);R4Audit::finish(s.post);
    auto post=Grid2D<double>(s.post,s.occ,s.m);auto mu=Utils::ExpectedValue(post,1);auto t5=Utils::ExpectedValue(post,.05);double v=Utils::Variance(post);
    bool first=!success&&v<1.5;if(first)success=true;
    ledger<<updates<<','<<count<<','<<v<<','<<mu.x<<','<<mu.y<<','<<t5.x<<','<<t5.y<<','<<first<<','<<Utils::r4_rng_state()<<','<<r4_gaussian_index()<<'\n';ledger.flush();updates++;
   }
  }
  s.mapdump(out/"final_map.csv");R4Audit::binary(out/"final_posterior.f64",s.post);
  std::ofstream(out/"EXECUTION.json")<<"{\"blocks\":"<<count<<",\"source_updates\":"<<updates<<",\"official_rule_would_converge\":"<<(success?"true":"false")<<",\"fixed_observation_shadow_continues_after_convergence\":true,\"navigation\":false}";
 }else throw std::runtime_error("unknown mode");
 std::cout<<"COMPLETE_NATIVE_CORE_OPERATOR\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
