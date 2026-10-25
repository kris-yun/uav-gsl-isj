#include <gaden/RunningSimulation.hpp>
#include <gaden/PlaybackSimulation.hpp>
#include <gaden/internal/Serialization.hpp>
#include <gaden/internal/compression.hpp>
#include <nlohmann/json.hpp>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <map>
#include <set>
#include <iostream>
using json=nlohmann::json;namespace fs=std::filesystem;
json readj(fs::path p){std::ifstream f(p);json j;f>>j;return j;}
struct Q{std::string id;int point;double time;gaden::Vector3 xyz;};
std::vector<std::string> split(std::string l){if(!l.empty()&&l.back()=='\r')l.pop_back();std::vector<std::string>a;std::stringstream s(l);std::string v;while(std::getline(s,v,','))a.push_back(v);return a;}
std::vector<Q> queries(fs::path path){std::ifstream f(path);std::string l;std::getline(f,l);auto h=split(l);std::map<std::string,int>ix;for(int i=0;i<h.size();i++)ix[h[i]]=i;std::vector<Q>r;while(std::getline(f,l)){auto a=split(l);if(a.size()<h.size())continue;r.push_back({a[ix["query_id"]],std::stoi(a[ix["point_id"]]),std::stod(a[ix["physical_s"]]),{std::stof(a[ix["x"]]),std::stof(a[ix["y"]]),std::stof(a[ix["z"]])}});}return r;}
void snapshot(gaden::Simulation& sim,fs::path dst){
 std::vector<uint8_t>raw(gaden::serialization::defaultBufferSize),compressed(raw.size()+1024);
 gaden::serialization::BufferWriter writer((char*)raw.data(),raw.size());
 writer.Write(&gaden::versionMajor);writer.Write(&gaden::versionMinor);writer.Write(&sim.config->environment.description);
 gaden::GasSource::SerializeBinary(writer,sim.simulationMetadata.source);writer.Write(&sim.simulationMetadata.constants);
 int wi=sim.config->windSequence.GetCurrentIndex();writer.Write(&wi);std::string mode="filaments";writer.WriteString(&mode);writer.WriteVector(&sim.GetFilaments());
 auto comp=gaden::serialization::CompressionMode::ZLIB;size_t n=writer.currentOffset();zlib::uLongf length=compressed.size();
 if(zlib::compress2(compressed.data(),&length,raw.data(),n,1)!=Z_OK)throw std::runtime_error("compression failed");
 std::ofstream out(dst,std::ios::binary);out.write(gaden::serialization::resultIdentifier,sizeof(gaden::serialization::resultIdentifier));out.write((char*)&comp,sizeof(comp));out.write((char*)&n,sizeof(n));out.write((char*)compressed.data(),length);
}
std::shared_ptr<gaden::EnvironmentConfiguration> environment(fs::path map,fs::path wind){
 auto c=std::make_shared<gaden::EnvironmentConfiguration>();if(c->environment.ReadFromFile(map)!=gaden::ReadResult::OK)throw std::runtime_error("bad geometry");std::vector<fs::path>w;
 for(auto&e:fs::directory_iterator(wind))if(e.is_regular_file())w.push_back(e.path());std::sort(w.begin(),w.end());if(w.size()!=1)throw std::runtime_error("requires original single E3 wind");c->windSequence.Initialize(w,c->environment.numCells(),{});return c;
}
struct OpenPlayback: gaden::PlaybackSimulation {using PlaybackSimulation::PlaybackSimulation;using Simulation::CheckLineOfSight;using Simulation::CalculateConcentrationSingleFilament;};
int main(int argc,char**argv){try{
 if(argc<6)throw std::runtime_error("physics mode config_or_query map wind_or_world out");
 std::string mode=argv[1];fs::path map=argv[3],location=argv[4],out=argv[5];fs::create_directories(out);
 if(mode=="generate"){
  auto task=readj(argv[2]);auto conf=environment(map,location);auto xyz=task.at("source_xyz");gaden::Vector3 source(xyz[0],xyz[1],xyz[2]);
  if(conf->environment.at(source)!=gaden::Environment::CellState::Free)throw std::runtime_error("source is not free");
  gaden::RunningSimulation::Parameters p;p.source=std::make_shared<gaden::PointSource>();p.source->sourcePosition=source;p.source->gasType=static_cast<gaden::GasType>(10);
  p.deltaTime=.1f;p.windIterationDeltaTime=1;p.temperature=298;p.pressure=1;p.filamentPPMcenter_initial=10;p.filamentInitialSigma=10;p.filamentGrowthGamma=15;p.filamentNoise_std=.015f;p.numFilaments_sec=10;p.expectedNumIterations=2400;p.saveResults=false;p.preCalculateConcentrations=false;p.windLoop=gaden::LoopConfig{};
  gaden::RunningSimulation sim(p,conf);auto qs=queries(task.at("query_csv"));std::vector<size_t>order(qs.size());std::iota(order.begin(),order.end(),0);std::sort(order.begin(),order.end(),[&](int a,int b){return qs[a].time<qs[b].time;});
  std::vector<float>values(qs.size());std::vector<int>binding(qs.size(),-1);std::vector<double>savedtime(qs.size());size_t cursor=0;int frame=0,step=0;
  fs::create_directories(out/"saved_world/wind");conf->windSequence.WriteToFiles(out/"saved_world/wind","wind_iteration");
  std::ofstream tl(out/"PHYSICAL_FRAME_TIME.csv"),rd(out/"RESPONSES.csv");tl<<"frame,physical_snapshot_time_s,post_step_time_s,wind_index_at_save,filaments_after_step\n"<<std::setprecision(17);
  double end=task.value("duration_s",240.);int iterations=std::ceil(end/.1);
  for(step=0;step<iterations;step++){
   double pre=sim.GetCurrentTime();sim.AdvanceTimestep();double post=sim.GetCurrentTime();bool needed=step==0||step==iterations-1;
   size_t begin=cursor;while(cursor<order.size()&&qs[order[cursor]].time<post-1e-8){if(qs[order[cursor]].time<pre-1e-6)throw std::runtime_error("query clock went backward");needed=true;cursor++;}
   if(needed){snapshot(sim,out/"saved_world"/("iteration_"+std::to_string(frame)));tl<<frame<<','<<pre<<','<<post<<','<<conf->windSequence.GetCurrentIndex()<<','<<sim.GetFilaments().size()<<'\n';
    for(size_t j=begin;j<cursor;j++){auto i=order[j];values[i]=sim.SampleConcentration(qs[i].xyz);binding[i]=frame;savedtime[i]=pre;}
    frame++;
   }
  }
  if(cursor!=order.size())throw std::runtime_error("query beyond240s");
  rd<<"query_id,point_id,physical_s,frame,snapshot_time_s,x,y,z,raw_gas_ppm\n"<<std::setprecision(17);
  for(size_t i=0;i<qs.size();i++)rd<<qs[i].id<<','<<qs[i].point<<','<<qs[i].time<<','<<binding[i]<<','<<savedtime[i]<<','<<qs[i].xyz.x<<','<<qs[i].xyz.y<<','<<qs[i].xyz.z<<','<<values[i]<<'\n';
  json result={{"status","NATIVE_GADEN_RUNNING_SIMULATION_COMPLETED"},{"source_xyz",xyz},{"iterations",iterations},{"snapshots",frame},{"queries",qs.size()},{"final_time",sim.GetCurrentTime()},{"gas_type",10},{"moles_per_filament",sim.simulationMetadata.constants.totalMolesInFilament},{"air_moles_per_cm3",sim.simulationMetadata.constants.numMolesAllGasesIncm3},{"full_true_wind_permission","physical generator/evaluator only"},{"native_transport_modified",false},{"RNG_initialization_instrumented",true}};
  std::ofstream(out/"GENERATOR_RESULT.json")<<std::setw(2)<<result<<'\n';std::cout<<result<<'\n';
 }else if(mode=="decompose"){
  auto conf=environment(map,location/"wind");std::ifstream fi(argv[2]);std::string l;std::getline(fi,l);auto h=split(l);std::map<std::string,int>ix;for(int i=0;i<h.size();i++)ix[h[i]]=i;
  std::ofstream summary(out/"DECOMPOSED_QUERIES.csv"),details(out/"FILAMENT_CONTRIBUTIONS.csv");summary<<"query_id,frame,x,y,z,native_ppm,sum_contributions_ppm,center_occupants_same_xy_cell,positive_contributors,ppm_from_centers_outside_xy_cell,nearest_center_m,nearest_sigma_cm,filaments,LOS_rejected_within_cutoff\n"<<std::setprecision(17);details<<"query_id,frame,filament_index,center_x,center_y,center_z,sigma_cm,distance_m,LOS,contribution_ppm,same_sensor_xy_cell\n"<<std::setprecision(17);
  int current=-1;std::unique_ptr<OpenPlayback>sim;auto flat=[](float x,float y){return std::pair<int,int>{int((x+5.5f)/.25f),int((y+6.f)/.25f)};};
  while(std::getline(fi,l)){auto a=split(l);int fr=std::stoi(a[ix["frame"]]);gaden::Vector3 point(std::stof(a[ix["x"]]),std::stof(a[ix["y"]]),std::stof(a[ix["z"]]));
   if(fr!=current){gaden::PlaybackSimulation::Parameters p;p.startIteration=fr;p.resultsDirectory=location;sim=std::make_unique<OpenPlayback>(p,conf,gaden::LoopConfig{});sim->AdvanceTimestep();current=fr;}
   float sum=0,outside=0;int n=0,cell=0,rejected=0;float nearest=1e30f,sigma=0;size_t k=0;
   for(const auto&f:sim->GetFilaments()){
    float dd=gaden::vmath::sqrlength(f.position-point);bool same=flat(point.x,point.y)==flat(f.position.x,f.position.y);if(same)cell++;
    if(dd<nearest){nearest=dd;sigma=f.sigma;}
    float limit=f.sigma*3/100.f;
    if(dd<limit*limit){bool los=sim->CheckLineOfSight(point,f.position);float pp=los?sim->CalculateConcentrationSingleFilament(f,point):0;sum+=pp;if(!same)outside+=pp;if(pp>0)n++;if(!los)rejected++;
     details<<a[ix["query_id"]]<<','<<fr<<','<<k<<','<<f.position.x<<','<<f.position.y<<','<<f.position.z<<','<<f.sigma<<','<<std::sqrt(dd)<<','<<los<<','<<pp<<','<<same<<'\n';
    }k++;
   }
   float raw=sim->SampleConcentration(point);if(raw!=sum)throw std::runtime_error("native concentration decomposition mismatch");
   summary<<a[ix["query_id"]]<<','<<fr<<','<<point.x<<','<<point.y<<','<<point.z<<','<<raw<<','<<sum<<','<<cell<<','<<n<<','<<outside<<','<<std::sqrt(nearest)<<','<<sigma<<','<<sim->GetFilaments().size()<<','<<rejected<<'\n';
  }
  std::cout<<"DECOMPOSITION_EXACT_NATIVE_SUM_PASS\n";
 }else throw std::runtime_error("bad mode");
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}}
