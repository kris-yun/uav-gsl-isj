// Native-only readback and playback. No RunningSimulation construction or step.
#include <gaden/EnvironmentConfiguration.hpp>
#include <gaden/EnvironmentConfigMetadata.hpp>
#include <gaden/PlaybackSimulation.hpp>
#include <gaden/RunningSimulation.hpp>
#include <gaden/internal/MathUtils.hpp>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <algorithm>
#include <cmath>
#include <cassert>
using namespace gaden;
struct Reader:PlaybackSimulation{using PlaybackSimulation::PlaybackSimulation;using Simulation::CalculateConcentrationSingleFilament;using Simulation::CheckLineOfSight;};
int main(int argc,char**argv){
  std::cout<<std::setprecision(17);
  std::string mode=argv[1];
  if(mode=="noise"){
    PrecalculatedGaussian<1000> g;float limit=0;std::ofstream out(argv[2],std::ios::binary);
    for(int i=0;i<1000;i++){float a=g.nextValue(0,1);limit=std::max(limit,std::abs(a));out.write((char*)&a,4);}
    std::cout<<"NOISE_MAX "<<limit<<"\n";return 0;
  }
  if(mode=="e0"){
    std::filesystem::path project=argv[2],output=argv[3];std::filesystem::create_directories(output);
    auto c=EnvironmentConfiguration::ReadDirectory(project);if(!c)return 4;auto&e=c->environment;auto n=e.description.dimensions;
    if(n.x!=240||n.y!=160||n.z!=96||e.description.cellSize!=.25f||e.description.minCoord.x!=-16||e.description.minCoord.y!=-20||e.description.minCoord.z!=-8||e.description.maxCoord.x!=44||e.description.maxCoord.y!=20||e.description.maxCoord.z!=16)return 5;
    for(auto q:c->localAirflowDisturbances)if(q.x!=0||q.y!=0||q.z!=0)return 16;
    size_t freeCount=0,outletCount=0;
    for(int z=0;z<n.z;z++)for(int y=0;y<n.y;y++)for(int x=0;x<n.x;x++){
      bool shell=x==0||y==0||z==0||x==n.x-1||y==n.y-1||z==n.z-1;
      auto state=e.at(Vector3i{x,y,z});if(state!=(shell?Environment::CellState::Outlet:Environment::CellState::Free))return 6;
      if(shell)outletCount++;else freeCount++;
    }
    const auto&w=c->windSequence.GetCurrent();if(w.size()!=e.numCells())return 7;
    static_assert(sizeof(Vector3)==12);int header[2]={3,0};std::ofstream b(output/"native_readback.wind",std::ios::binary);b.write((char*)header,8);b.write((char*)w.data(),w.size()*sizeof(Vector3));b.close();
    EnvironmentConfigMetadata metadata(project);if(metadata.ReadDirectory()!=ReadResult::OK)return 8;
    std::ofstream params(output/"effective_params.tsv");params<<std::setprecision(17)<<"id\tx\ty\tz\tgas\tdt\twind_dt\tT\tP\tppm\tsigma_cm\tgamma\tnoise_input\trelease\titerations\tsave\tsave_dt\tprecalculate\tloop\tfrom\tto\toutput\n";
    for(auto const&id:metadata.simulations){auto p=metadata.GetSimulationParams(id);auto q=p.source->sourcePosition;if(e.at(q)!=Environment::CellState::Free||std::string(p.source->Type())!="point")return 17;
      params<<id<<'\t'<<q.x<<'\t'<<q.y<<'\t'<<q.z<<'\t'<<(int)p.source->gasType<<'\t'<<p.deltaTime<<'\t'<<p.windIterationDeltaTime<<'\t'<<p.temperature<<'\t'<<p.pressure<<'\t'<<p.filamentPPMcenter_initial<<'\t'<<p.filamentInitialSigma<<'\t'<<p.filamentGrowthGamma<<'\t'<<p.filamentNoise_std<<'\t'<<p.numFilaments_sec<<'\t'<<p.expectedNumIterations<<'\t'<<p.saveResults<<'\t'<<p.saveDeltaTime<<'\t'<<p.preCalculateConcentrations<<'\t'<<(p.windLoop?p.windLoop->loop:0)<<'\t'<<(p.windLoop?p.windLoop->from:0)<<'\t'<<(p.windLoop?p.windLoop->to:0)<<'\t'<<p.saveDataDirectory.string()<<'\n';
    }
    std::cout<<"E0_READBACK_OK free="<<freeCount<<" outlet="<<outletCount<<" count="<<w.size()<<"\n";return 0;
  }
  if(mode!="e1")return 9;
  std::filesystem::path project=argv[2],result=argv[3],outdir=argv[4];std::filesystem::create_directories(outdir);
  auto c=EnvironmentConfiguration::ReadDirectory(project);Reader sim({0,result},c,{false,0,0});auto&e=c->environment;
  std::ifstream times(result/"RECORD_TIMELINE.tsv");std::string line;getline(times,line);
  std::ofstream states(outdir/"filament_states.f32",std::ios::binary),frames(outdir/"native_frames.csv");frames<<"record_index,time_s,wind_index,n_filaments,offset_filaments\n";size_t offset=0;
  while(getline(times,line)){std::istringstream s(line);size_t idx;double t;int wi;s>>idx>>t>>wi;if(!sim.LoadIteration(idx))return 10;auto&f=sim.GetFilaments();states.write((char*)f.data(),f.size()*sizeof(Filament));frames<<std::setprecision(17)<<idx<<','<<t<<','<<wi<<','<<f.size()<<','<<offset<<'\n';offset+=f.size();}
  states.close();frames.close();
  static_assert(sizeof(Filament)==16);
  // Continuous-coordinate observations, exactly the frozen geometry-only route CSV.
  std::ifstream route(argv[5]);getline(route,line);std::ofstream obs(outdir/"route.csv"),parity(outdir/"sampling_parity.csv");obs<<"time_s,record_index,x,y,z,ppm\n";parity<<"time_s,point_kind,point_id,native,scatter,absolute_difference\n";
  std::vector<std::pair<double,size_t>> clock;std::ifstream fr(outdir/"native_frames.csv");getline(fr,line);while(getline(fr,line)){for(char&ch:line)if(ch==',')ch=' ';std::istringstream ss(line);size_t k,nn,off;double t;int wi;ss>>k>>t>>wi>>nn>>off;clock.push_back({t,k});}
  while(getline(route,line)){
    for(char&ch:line)if(ch==',')ch=' ';std::istringstream r(line);double t;Vector3 xyz;r>>t>>xyz.x>>xyz.y>>xyz.z;
    auto at=std::upper_bound(clock.begin(),clock.end(),t,[](double a,auto const&b){return a<b.first;});if(at==clock.begin())return 11;--at;if(t-at->first>.61)return 12;if(!sim.LoadIteration(at->second))return 13;
    float val=sim.SampleConcentration(xyz);obs<<std::setprecision(17)<<t<<','<<at->second<<','<<xyz.x<<','<<xyz.y<<','<<xyz.z<<','<<val<<'\n';
    // ROI concentration scatter: native cell-centres every two cells, full Free z column.
    const int NX=40,NY=32,NZ=48;std::vector<float> grid(NX*NY*NZ,0);std::vector<Vector3> coords(grid.size());
    auto slot=[](int x,int y,int z){return x+40*y+40*32*z;};
    for(int iz=0;iz<NZ;iz++)for(int iy=0;iy<NY;iy++)for(int ix=0;ix<NX;ix++){auto id=Vector3i{56+2*ix,48+2*iy,2*iz};coords[slot(ix,iy,iz)]=e.coordsOfCellCenter(id);}
    for(auto const&fil:sim.GetFilaments()){
      float rad=fil.sigma*3/100.f,r2=rad*rad;auto low=e.coordsToIndices(fil.position-Vector3{rad,rad,rad}),high=e.coordsToIndices(fil.position+Vector3{rad,rad,rad});
      for(int iz=std::max(1,(low.z+1)/2);iz<=std::min(47,high.z/2);iz++)for(int iy=std::max(0,(low.y-48+1)/2);iy<=std::min(31,(high.y-48)/2);iy++)for(int ix=std::max(0,(low.x-56+1)/2);ix<=std::min(39,(high.x-56)/2);ix++){
        int k=slot(ix,iy,iz);auto q=coords[k];if(vmath::sqrlength(fil.position-q)<r2&&sim.CheckLineOfSight(q,fil.position))grid[k]+=sim.CalculateConcentrationSingleFilament(fil,q);
      }
    }
    auto verify=[&](int k,const char*kind){float native=sim.SampleConcentration(coords[k]),diff=std::abs(native-grid[k]);parity<<std::setprecision(17)<<t<<','<<kind<<','<<k<<','<<native<<','<<grid[k]<<','<<diff<<'\n';return diff<=1e-5*(1+std::abs(native));};
    for(int j=0;j<25;j++)if(!verify(j*(grid.size()-1)/24,"fixed"))return 14;
    std::vector<int> nz;for(int k=0;k<(int)grid.size();k++)if(grid[k]>0)nz.push_back(k);for(int j=0;j<std::min(25,(int)nz.size());j++)if(!verify(nz[j*(nz.size()-1)/std::max(1,std::min(25,(int)nz.size())-1)],"nonzero"))return 15;
    std::ofstream column(outdir/("roi_column_t"+std::to_string((int)t)+".f32"),std::ios::binary);std::vector<float> col(NX*NY,0);for(int iz=1;iz<NZ;iz++)for(int xy=0;xy<NX*NY;xy++)col[xy]+=grid[xy+NX*NY*iz]*.5f;column.write((char*)col.data(),col.size()*4);
  }
  std::cout<<"E1_NATIVE_PLAYBACK_COMPLETE\n";return 0;
}
