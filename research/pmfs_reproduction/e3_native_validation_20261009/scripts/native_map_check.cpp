#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <fstream>
#include <iomanip>
#include <iostream>
using namespace GSL;
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("raw map and output required");
 std::ifstream f(argv[1]);nav_msgs::msg::OccupancyGrid map;
 double ox,oy,res;int width,height;
 f>>width>>height>>res>>ox>>oy;map.info.width=width;map.info.height=height;map.info.resolution=res;map.info.origin.position.x=ox;map.info.origin.position.y=oy;
 int val;while(f>>val)map.data.push_back(val);if(map.data.size()!=width*height)throw std::runtime_error("map count");
 Grid2DMetadata m;PMFSLib::InitMetadata(m,map,25);std::vector<Occupancy> occ(m.dimensions.x*m.dimensions.y);
 GridUtils::reduceOccupancyMap(map.data,map.info.width,occ,m);
 m.numFreeCells=PMFSLib::PruneUnreachableCells(occ,m,{-3,4.5});
 auto ij=m.coordinatesToIndices({-4,-1.9});bool free=occ.at(m.indexOf(ij))==Occupancy::Free;
 std::ofstream o(argv[2]);o<<std::setprecision(17)<<"{\"width\":"<<m.dimensions.x<<",\"height\":"<<m.dimensions.y<<",\"cell_size\":"<<m.cellSize<<",\"origin\":["<<m.origin.x<<","<<m.origin.y<<"],\"free_cells\":"<<m.numFreeCells<<",\"source_ij\":["<<ij.x<<","<<ij.y<<"],\"source_supported\":"<<(free?"true":"false")<<",\"core_calls\":[\"InitMetadata\",\"reduceOccupancyMap\",\"PruneUnreachableCells\"],\"propagation_simulations\":0,\"native_goals\":0}";
 return free?0:2;
}catch(std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
