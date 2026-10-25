#include <bits/stdc++.h>
#include <gaden/Simulation.hpp>
#include <gaden/internal/compression.hpp>
#include <nlohmann/json.hpp>
using json=nlohmann::json;
struct Kernel: gaden::Simulation {using Simulation::Simulation;using Simulation::CheckLineOfSight;using Simulation::CalculateConcentrationSingleFilament;std::vector<gaden::Filament>f;void AdvanceTimestep()override{}const std::vector<gaden::Filament>&GetFilaments()const override{return f;}};
int main(int argc,char**argv){try{
 if(std::string(argv[1])=="cache"){
  std::ifstream fi(argv[2]);json j;fi>>j;std::vector<uint32_t>w=j["cache_seed_words"].get<std::vector<uint32_t>>();std::seed_seq s(w.begin(),w.end());std::mt19937 e(s);std::normal_distribution<>n(0,1);std::ofstream initial(std::string(argv[3])+".initial.txt");initial<<e<<"\nnormal="<<n<<'\n';std::vector<float>a(2500);for(auto&v:a)v=n(e);std::ofstream out(argv[3],std::ios::binary);out.write((char*)a.data(),a.size()*4);std::ofstream fin(std::string(argv[3])+".final.txt");fin<<e<<"\nnormal="<<n<<'\n';return 0;
 }
 if(argc!=6)throw std::runtime_error("kernel trace map points constants outCSV");
 auto config=std::make_shared<gaden::EnvironmentConfiguration>();if(config->environment.ReadFromFile(argv[2])!=gaden::ReadResult::OK)throw std::runtime_error("bad map");Kernel k(config);
 std::ifstream jf(argv[4]);json j;jf>>j;k.simulationMetadata.constants.totalMolesInFilament=j["moles_per_filament"].get<float>();k.simulationMetadata.constants.numMolesAllGasesIncm3=j["air_moles_per_cm3"].get<float>();
 std::ifstream pf(argv[3]);std::string l;std::getline(pf,l);std::vector<gaden::Vector3>points;
 while(std::getline(pf,l)){std::replace(l.begin(),l.end(),',',' ');std::stringstream ss(l);int id;float x,y,z;if(ss>>id>>x>>y>>z){if(id!=points.size())throw std::runtime_error("point ordering");points.emplace_back(x,y,z);}}
 std::ifstream trace(argv[1],std::ios::binary);std::ofstream out(argv[5]);out<<"step,point_id,ppm,center_hit,active_filaments,physical3D_rejected_centers\n"<<std::setprecision(17);
 while(true){uint32_t step,count;trace.read((char*)&step,4);if(!trace)break;trace.read((char*)&count,4);std::vector<std::array<float,4>>f(count);trace.read((char*)f.data(),count*16);if(!trace)throw std::runtime_error("truncated trace");
  std::vector<float>values(points.size(),0);std::vector<int>hits(points.size(),0);int invalid=0;
  for(auto a:f){gaden::Filament fil(a[0],a[1],.7f,a[2]);bool free=config->environment.at(fil.position)==gaden::Environment::CellState::Free;if(!free)invalid++;
   for(int p=0;p<points.size();p++){
    if(int((points[p].x+5.5f)/.25f)==int((fil.position.x+5.5f)/.25f)&&int((points[p].y+6.f)/.25f)==int((fil.position.y+6.f)/.25f))hits[p]=1;
    float distance=gaden::vmath::sqrlength(fil.position-points[p]);float limit=fil.sigma*3/100.f;
    if(distance<limit*limit&&k.CheckLineOfSight(points[p],fil.position))values[p]+=k.CalculateConcentrationSingleFilament(fil,points[p])*a[3];
   }
  }
  for(int p=0;p<points.size();p++)out<<step<<','<<p<<','<<values[p]<<','<<hits[p]<<','<<count<<','<<invalid<<'\n';
 }
 std::cout<<"KERNEL_WITH_NATIVE_3D_LOS_AND_CONCENTRATION_COMPLETED\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}}
