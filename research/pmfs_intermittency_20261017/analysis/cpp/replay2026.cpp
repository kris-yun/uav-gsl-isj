#include "native_support.hpp"
using namespace GSL;
bool pathFree(Grid2DMetadata m,const std::vector<Occupancy>&o,Vector2Int a,Vector2Int b){
 auto x=m.indicesToCoordinates(a),y=m.indicesToCoordinates(b),d=y-x;
 auto ray=DDA::_2D::castRay<Occupancy>(x,d,vmath::length(d),DDA::_2D::Map<Occupancy>(o,m.origin,m.cellSize,m.dimensions),[](auto v){return v==Occupancy::Free;});return !ray.hitSomething;
}
int main(int argc,char**argv){
 if(argc!=3)return 2;std::ifstream in(argv[1]);std::ofstream out(argv[2],std::ios::binary);
 Grid2DMetadata m{};int nf,nw;in>>m.dimensions.x>>m.dimensions.y>>m.origin.x>>m.origin.y>>m.cellSize>>nf>>nw;m.numFreeCells=nf;m.scale=25;
 PMFS_internal::HitProbabilitySettings s;in>>s.prior>>s.kernelSigma>>s.kernelStretchConstant>>s.confidenceSigmaSpatial>>s.confidenceMeasurementWeight>>s.localEstimationWindowSize;
 std::vector<int>free(nf);std::vector<Occupancy>occ(m.dimensions.x*m.dimensions.y,Occupancy::Obstacle);
 for(auto&i:free){in>>i;occ[i]=Occupancy::Free;}
 std::vector<PMFS_internal::HitProbability>state(occ.size());for(auto&v:state){v.logOdds=log(s.prior/(1-s.prior));v.auxWeight=-1;}
 Grid2D<PMFS_internal::HitProbability>g{state,occ,m};VisibilityMap vis(m.dimensions.x,m.dimensions.y,5);
 for(int y=0;y<m.dimensions.y;++y)for(int x=0;x<m.dimensions.x;++x){Vector2Int a{x,y};std::vector<Vector2Int>vv;
  if(g.freeAt(x,y))for(int yy=std::max(0,y-5);yy<=std::min(m.dimensions.y-1,y+5);++yy)for(int xx=std::max(0,x-5);xx<=std::min(m.dimensions.x-1,x+5);++xx){Vector2Int b{xx,yy};if(g.freeAt(xx,yy)&&(a==b||pathFree(m,occ,a,b)))vv.push_back(b);}vis.emplace(a,vv);}
 for(int k=0;k<nw;++k){float px,py;int hit;double speed,dir;in>>px>>py>>hit>>speed>>dir;if(!in)return 3;auto pos=m.coordinatesToIndices(px,py);if(!m.indicesInBounds(pos)||!g.freeAt(pos.x,pos.y))return 4;
  PMFSLib::EstimateHitProbabilities(g,vis,s,hit,dir,speed,pos);
  double angle=-angles::normalize_angle(dir+M_PI/2);Vector2 sigma{s.kernelSigma/(1+s.kernelStretchConstant*speed/s.kernelSigma),s.kernelSigma+s.kernelStretchConstant*speed};
  for(int idx:free){auto&v=state[idx];Vector2 offset=v.distanceFromRobot==0?Vector2{0,0}:v.originalPropagationDirection*float(v.distanceFromRobot);double w=Utils::evaluate2DGaussian(offset,sigma,angle)/Utils::evaluate2DGaussian({0,0},sigma,angle);double coverage=Utils::evaluate1DGaussian(v.distanceFromRobot,s.confidenceSigmaSpatial);double row[]={v.logOdds,v.confidence,w,coverage};out.write((char*)row,sizeof(row));}
 }
 if(!out)return 5;return 0;
}
