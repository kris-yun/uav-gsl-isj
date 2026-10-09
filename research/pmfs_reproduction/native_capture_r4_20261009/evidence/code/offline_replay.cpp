#include "Fixture.hpp"
#include <tf2/LinearMath/Quaternion.h>
#include <omp.h>
namespace GSL::PMFS_internal {
void r4_set_gaussian(const std::array<float,2500>&,uint16_t);
uint16_t r4_gaussian_index();
}
using namespace R4;
class Forward : public Simulations {
public:
 using Simulations::Simulations;
 std::pair<long double,std::vector<float>> replay(const Utils::NQA::Node& leaf,const fs::path& out,const std::string& id) {
  std::vector<float> map(measuredHitProb.data.size(),0.0f);SimulationSource source(&leaf,measuredHitProb.metadata);
  simulateSourceInPosition(source,map,true,settings.iterationsToRecord,settings.deltaTime,settings.noiseSTDev);
  R4Audit::binary(out/(id+"_unblurred.f32"),map);
  if(settings.blurSigmaX>0||settings.blurSigmaY>0){cv::Mat m(map);m=m.reshape(1,measuredHitProb.metadata.dimensions.y);blurHitMap(m);}
  return {sourceProbFromMaps(measuredHitProb,map),map};
 }
};
static void rebuildMeasurements(Fixture& f,const fs::path& native,const fs::path& out) {
 auto raw=csv(native/"raw_consumed_messages.csv"),events=csv(native/"measurement_events.csv");
 if(raw.size()!=18||events.size()!=3)throw std::runtime_error("fresh raw input shape");
 std::ofstream audit(out/"measurement_blocks.csv");audit<<std::setprecision(17)<<"block_id,gas_members,wind_members,concentration,wind_speed,wind_direction,hit,independent_TF_angle_max_abs\n";
 for(int block=1;block<=3;++block){std::vector<double> gas,speed,direction;double tfError=0;
  for(const auto& r:raw){if(integer(r,"block_id")!=block)continue;
   if(r.at("kind")=="gas"){
    if(integer(r,"raw_units")!=3)throw std::runtime_error("fixture raw gas unit not PPM");float ppm=d(r,"raw");if(double(ppm)!=d(r,"ppm"))throw std::runtime_error("gas conversion diverged");gas.push_back(ppm);
   }else{
    tf2::Quaternion sensor,local;sensor.setRPY(0,0,d(r,"sample_yaw"));local.setRPY(0,0,d(r,"local_direction"));auto q=sensor*local;
    double yaw=std::atan2(2*(q.w()*q.z()+q.x()*q.y()),1-2*(q.y()*q.y()+q.z()*q.z()));double delta=std::atan2(std::sin(yaw-d(r,"map_TO_direction")),std::cos(yaw-d(r,"map_TO_direction")));tfError=std::max(tfError,std::abs(delta));
    if(tfError>1e-12)throw std::runtime_error("independent saved TF transform diverged");
    speed.push_back(float(d(r,"speed")));direction.push_back(float(d(r,"map_TO_direction")));
   }
  }
  if(gas.size()!=3||speed.size()!=3)throw std::runtime_error("block raw membership");
  double concentration=Utils::getAverageFloatCollection(gas.begin(),gas.end());double s=Utils::getAverageFloatCollection(speed.begin(),speed.end());double a=Utils::getAverageDirection(direction.begin(),direction.end());bool hit=concentration>.1;
  const auto& e=events.at(block-1);
  if(concentration!=d(e,"concentration")||s!=d(e,"wind_speed")||a!=d(e,"wind_direction")||hit!=integer(e,"hit"))throw std::runtime_error("raw-to-measurement-block first divergence");
  auto ij=f.meta.coordinatesToIndices(float(d(e,"robot_x")),float(d(e,"robot_y")));if(ij.x!=integer(e,"robot_i")||ij.y!=integer(e,"robot_j"))throw std::runtime_error("measurement coordinates diverged");
  f.measurement(hit,a,s,ij);f.dumpHit(out/("hit_after_block_"+std::to_string(block)+".csv"));audit<<block<<",3,3,"<<concentration<<","<<s<<","<<a<<","<<hit<<","<<tfError<<"\n";
 }
 f.dumpHit(out/"hit_before_update.csv");
}
int main(int argc,char**argv) {
 try{
  if(argc!=4)throw std::runtime_error("offline INPUT NATIVE_CAPTURE OUTPUT");fs::path input=argv[1],native=argv[2],out=argv[3];if(fs::exists(out))throw std::runtime_error("offline output exists");fs::create_directories(out);
  if(omp_get_max_threads()!=1)throw std::runtime_error("replay threads must be 1");Fixture f(input);rebuildMeasurements(f,native,out);
#if R4_FORWARD
  auto sim=f.simulation<Forward>();f.restoreCapturedTree(*sim,native);auto candidates=csv(native/"candidates.csv");
  std::array<float,2500> cache;std::ifstream cacheFile(native/"gaussian_cache.f32",std::ios::binary);cacheFile.read(reinterpret_cast<char*>(cache.data()),sizeof(cache));if(!cacheFile||cacheFile.peek()!=EOF)throw std::runtime_error("cache shape");
  auto initial=csv(native/"gaussian_initial.csv");std::vector<std::vector<uint8_t>> occupancyMap(f.meta.dimensions.x,std::vector<uint8_t>(f.meta.dimensions.y));
  for(int i=0;i<f.meta.dimensions.x;++i)for(int j=0;j<f.meta.dimensions.y;++j)occupancyMap[i][j]=f.hitGrid().freeAt(i,j)?1:0;
  fs::create_directories(out/"maps");std::ofstream scores(out/"candidate_scores.csv");scores<<std::setprecision(21)<<"serial,candidate_id,score,logscore,points_used,gaussian_index_after\n";
  for(const auto& r:candidates){std::string id=r.at("candidate_id");size_t count=std::stoul(r.at("point_count"));std::ifstream p(native/r.at("points_file"),std::ios::binary);std::vector<float> pairs(count*2);p.read(reinterpret_cast<char*>(pairs.data()),pairs.size()*sizeof(float));if(!p||p.peek()!=EOF)throw std::runtime_error("point shape");R4Replay::points.clear();R4Replay::points.reserve(count);for(size_t i=0;i<count;++i)R4Replay::points.emplace_back(pairs[i*2],pairs[i*2+1]);R4Replay::offset=0;R4Replay::enabled=true;
   uint16_t index=integer(r,"gaussian_ready_before")?integer(r,"gaussian_index_before"):integer(initial.at(0),"index");r4_set_gaussian(cache,index);Utils::r4_rng_restore(r.at("rng_before"));
   Utils::NQA::Node leaf(nullptr,{integer(r,"origin_i"),integer(r,"origin_j")},{integer(r,"size_i"),integer(r,"size_j")},occupancyMap);
   auto result=sim->replay(leaf,out/"maps",id);if(R4Replay::offset!=count||r4_gaussian_index()!=integer(r,"gaussian_index_after"))throw std::runtime_error("sample/noise consumption diverged "+id);
   R4Audit::binary(out/"maps"/(id+".f32"),result.second);scores<<r.at("serial")<<","<<id<<","<<result.first<<","<<std::log(result.first)<<","<<R4Replay::offset<<","<<r4_gaussian_index()<<"\n";
  }
  std::ofstream(out/"FORWARD_COMPLETE.json")<<"{\"per_candidate_forward_replays\":"<<candidates.size()<<",\"uses_actual_saved_points_and_gaussian_cache\":true}\n";
#else
  auto sim=f.simulation();f.restoreCapturedTree(*sim,native);std::string state;std::ifstream(native/"rng_before_update.txt")>>state;Utils::r4_rng_restore(state);
  sim->updateSourceProbability(float(f.sim.refineFraction));f.dumpPosterior(out);R4Audit::binary(out/"variance.f64",sim->varianceOfHitProb);
  fs::create_directories(out/"coarse_maps");size_t valid=0;
  for(const auto& leaf:sim->QTleaves)if(leaf.value==1){if(valid>=sim->resultsFirstLevel.size())throw std::runtime_error("coarse result identity mismatch");R4Audit::binary(out/"coarse_maps"/(R4Audit::id(&leaf)+".f32"),sim->resultsFirstLevel[valid++].hitMap);}
  if(valid!=sim->resultsFirstLevel.size())throw std::runtime_error("coarse result count mismatch");
  std::ofstream(out/"CONTROL_COMPLETE.json")<<"{\"uninstrumented_full_source_updates\":1,\"coarse_results\":"<<sim->resultsFirstLevel.size()<<",\"same_captured_RNG_pre_state\":true}\n";
#endif
  return 0;
 }catch(const std::exception& e){std::cerr<<"R4_REPLAY_ERROR: "<<e.what()<<"\n";return 1;}
}
