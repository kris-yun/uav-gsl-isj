#include <gaden/PlaybackSimulation.hpp>
#include <fstream>
#include <iostream>
#include <iomanip>
using namespace gaden;
int main(int argc,char**argv){
 auto c=std::make_shared<EnvironmentConfiguration>();
 c->environment.ReadFromFile(argv[1]); auto&e=c->environment;
 if(argc==3){std::ofstream f(argv[2]); f<<"ix,iy,x,y,z\n";
  int iz=e.coordsToIndices(Vector3{0,0,.2f}).z;
  for(int x=0;x<e.description.dimensions.x;x++)for(int y=0;y<e.description.dimensions.y;y++)
   if(e.at(Vector3i{x,y,iz})==Environment::CellState::Free){auto q=e.coordsOfCellCenter({x,y,iz});f<<x<<','<<y<<','<<q.x<<','<<q.y<<','<<q.z<<'\n';}return 0;}
 std::vector<std::filesystem::path> winds;for(int i=0;i<=10;i++)winds.push_back(std::string(argv[2])+"/wind/wind_iteration_"+std::to_string(i));
 c->windSequence.Initialize(winds,e.numCells(),{false,0,0});
 PlaybackSimulation sim({0,argv[2]},c,{false,0,0});
 std::ifstream route(argv[3]);std::ofstream out(argv[4]);std::string line;getline(route,line);
 out<<std::setprecision(9)<<"time,record_index,x,y,z,u,v,w,concentration\n";
 while(getline(route,line)){for(auto&ch:line)if(ch==',')ch=' ';std::istringstream s(line);double t;size_t i;Vector3 q;s>>t>>i>>q.x>>q.y>>q.z;
  if(e.at(q)!=Environment::CellState::Free||!sim.LoadIteration(i))return 4;
  auto w=sim.SampleWind(q);out<<t<<','<<i<<','<<q.x<<','<<q.y<<','<<q.z<<','<<w.x<<','<<w.y<<','<<w.z<<','<<sim.SampleConcentration(q)<<'\n';}
}
