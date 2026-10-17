#include "native_support.hpp"
using namespace GSL;
int main(int argc,char**argv){if(argc!=2)return 2;std::ifstream in(argv[1]);int groups;in>>groups;std::cout<<std::setprecision(17)<<"group,mean_x,mean_y,top5_x,top5_y,variance_m2\n";
for(int k=0;k<groups;++k){Grid2DMetadata m{};int nf;in>>m.dimensions.x>>m.dimensions.y>>m.origin.x>>m.origin.y>>m.cellSize>>nf;std::vector<double>data(m.dimensions.x*m.dimensions.y,0);std::vector<Occupancy>occ(data.size(),Occupancy::Obstacle);for(int j=0;j<nf;++j){int idx;double p;in>>idx>>p;data[idx]=p;occ[idx]=Occupancy::Free;}if(!in)return 3;Grid2D<double>g{data,occ,m};auto mean=Utils::ExpectedValue(g,1),top=Utils::ExpectedValue(g,.05);std::cout<<k<<','<<mean.x<<','<<mean.y<<','<<top.x<<','<<top.y<<','<<Utils::Variance(g)<<'\n';}
}
