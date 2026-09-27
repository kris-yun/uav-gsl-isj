// Calls the actual unmodified Native PMFSLib legality function, not a new rule.
#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <fstream>
#include <iostream>
#include <vector>
int main(int argc,char**argv){
 if(argc!=10)return 2;
 GSL::Grid2DMetadata m;m.dimensions={std::stoi(argv[1]),std::stoi(argv[2])};m.cellSize=std::stof(argv[3]);
 m.origin={std::stof(argv[4]),std::stof(argv[5])};m.scale=3;m.numFreeCells=0;
 std::ifstream f(argv[8],std::ios::binary);std::vector<unsigned char>b((std::istreambuf_iterator<char>(f)),{});
 if(b.size()!=size_t(m.dimensions.x*m.dimensions.y))return 3;
 std::vector<GSL::Occupancy>o;for(auto v:b)o.push_back(static_cast<GSL::Occupancy>(v));
 auto n=GSL::PMFSLib::PruneUnreachableCells(o,m,{std::stof(argv[6]),std::stof(argv[7])});
 std::ofstream out(argv[9],std::ios::binary);for(auto v:o){unsigned char c=static_cast<unsigned char>(v);out.write(reinterpret_cast<char*>(&c),1);}
 if(!out)return 4;std::cout<<"NATIVE_LEGAL_COUNT "<<n<<'\n';return 0;
}
