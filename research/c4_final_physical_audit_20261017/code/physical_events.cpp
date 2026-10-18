// Offline same-frame event audit. No advection, no new worlds, no ROS node.
// Concentration and visibility call the original R6 libgaden functions.
#include <gaden/Simulation.hpp>
#include <zlib.h>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <map>
#include <cstring>
#include <chrono>
#include <cmath>
#include <iostream>
namespace fs=std::filesystem;
using Row=std::map<std::string,std::string>;
std::vector<std::string> split(std::string s){std::vector<std::string>a;std::stringstream ss(s);std::string v;while(std::getline(ss,v,','))a.push_back(v);if(!s.empty()&&s.back()==',')a.emplace_back();return a;}
std::vector<Row> csv(fs::path p){std::ifstream f(p);std::string s;std::getline(f,s);if(!s.empty()&&s.back()=='\r')s.pop_back();auto h=split(s);std::vector<Row> a;while(std::getline(f,s)){if(!s.empty()&&s.back()=='\r')s.pop_back();auto v=split(s);if(v.size()!=h.size())throw std::runtime_error("CSV shape "+p.string());Row r;for(size_t k=0;k<v.size();k++)r[h[k]]=v[k];a.push_back(r);}return a;}
struct Saved: gaden::Simulation{
 std::vector<gaden::Filament> filaments;
 Saved(std::shared_ptr<gaden::EnvironmentConfiguration> c):Simulation(c){}
 void AdvanceTimestep() override{}
 const std::vector<gaden::Filament>& GetFilaments()const override{return filaments;}
 using Simulation::CheckLineOfSight; using Simulation::CalculateConcentrationSingleFilament;
 void load(fs::path p){
  std::ifstream f(p,std::ios::binary);std::vector<unsigned char>b((std::istreambuf_iterator<char>(f)),{});
  if(b.size()<22||memcmp(b.data(),"GADEN_RESULT",13)||b[13]!=1)throw std::runtime_error("Frame header");
  uint64_t size;memcpy(&size,b.data()+14,8);std::vector<unsigned char>raw(size);zlib::uLongf n=size;
  if(zlib::uncompress(raw.data(),&n,b.data()+22,b.size()-22)!=Z_OK||n!=size)throw std::runtime_error("Frame compression");
  size_t o=0;auto read=[&](void*dest,size_t n){if(o+n>raw.size())throw std::runtime_error("Truncated frame");memcpy(dest,raw.data()+o,n);o+=n;};
  int version[2];read(version,8);if(version[0]!=3||version[1]!=0)throw std::runtime_error("Frame version");
  gaden::Environment::Description desc;read(&desc,sizeof(desc));
  if(memcmp(&desc,&config->environment.description,sizeof(desc)))throw std::runtime_error("Geometry description differs");
  uint64_t len;read(&len,8);std::string type(len,' ');read(type.data(),len);if(type!="point")throw std::runtime_error("Source type");
  gaden::Vector3 source;read(&source,sizeof(source));int gas;read(&gas,4);if(gas!=10)throw std::runtime_error("Gas type");
  read(&simulationMetadata.constants,sizeof(simulationMetadata.constants));int wind;read(&wind,4);
  read(&len,8);std::string mode(len,' ');read(mode.data(),len);if(mode!="filaments")throw std::runtime_error("Frame mode");
  read(&len,8);filaments.resize(len);read(filaments.data(),len*sizeof(gaden::Filament));if(o!=raw.size())throw std::runtime_error("Frame trailer");
 }
};
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("physical_events STUDY OUTPUT.csv");fs::path R=argv[1];
 auto c=std::make_shared<gaden::EnvironmentConfiguration>();c->environment.ReadFromFile(R/"inputs/OccupancyGrid3D.csv");Saved sim(c);
 auto m=csv(R/"inputs/C4_update_1/metadata.csv").at(0);float ox=std::stof(m.at("origin_x")),oy=std::stof(m.at("origin_y")),step=std::stof(m.at("cell_size"));
 std::ofstream out(argv[2]);out<<std::setprecision(17);
 out<<"serial,frame,recomputed_ppm,recorded_ppm,absolute_ppm_error,native_projected_centres,native_xy_sensor_slab_centres,physical_voxel_centres,contributing_filaments,ppm_from_outside_native_xy,ppm_from_outside_sensor_slab,contribution_weighted_abs_dz_m,min_centre_distance_m,active_filaments,cpu_s\n";
 int cached=-1;
 for(auto &r:csv(R/"inputs/physical_queries.csv")){
  int frame=std::stoi(r.at("frame"));if(frame!=cached){sim.load(R/"inputs/physical_frames"/("iteration_"+std::to_string(frame)));cached=frame;}
  gaden::Vector3 p(std::stof(r.at("x")),std::stof(r.at("y")),std::stof(r.at("z")));
  auto begin=std::clock();float ppm=sim.SampleConcentration(p);int ix=int((p.x-ox)/step),iy=int((p.y-oy)/step);auto pi=c->environment.coordsToIndices(p);
  int xy=0,slab=0,voxel=0,contrib=0;double outsideXY=0,outsideZ=0,wdz=0,total=0,minD=1e30;
  for(auto&fil:sim.filaments){
   bool sameXY=int((fil.position.x-ox)/step)==ix&&int((fil.position.y-oy)/step)==iy;
   bool sameZ=fil.position.z>=p.z-step*.5f&&fil.position.z<p.z+step*.5f;
   xy+=sameXY;slab+=sameXY&&sameZ;voxel+=c->environment.coordsToIndices(fil.position)==pi;
   float d2=gaden::vmath::sqrlength(fil.position-p);minD=std::min(minD,double(std::sqrt(d2)));
   float limit=fil.sigma*3/100.f;
   if(d2<limit*limit&&sim.CheckLineOfSight(p,fil.position)){
    float v=sim.CalculateConcentrationSingleFilament(fil,p);++contrib;total+=v;
    if(!sameXY)outsideXY+=v;if(!sameZ)outsideZ+=v;wdz+=v*std::abs(fil.position.z-p.z);
   }
  }
  double original=std::stod(r.at("recorded_service_ppm"));
  out<<r.at("serial")<<","<<frame<<","<<ppm<<","<<original<<","<<std::abs(ppm-original)<<","<<xy<<","<<slab<<","<<voxel<<","<<contrib<<","<<outsideXY<<","<<outsideZ<<","<<(total?wdz/total:0)<<","<<minD<<","<<sim.filaments.size()<<","<<double(std::clock()-begin)/CLOCKS_PER_SEC<<"\n";
 }
 return 0;
 }catch(std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
