#pragma once
#include "Audit.hpp"
#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <map>
#include <algorithm>
#include <numeric>
#include <iostream>

namespace R4 {
using namespace GSL;
using namespace GSL::PMFS_internal;
namespace fs=std::filesystem;
using Row=std::map<std::string,std::string>;
inline std::vector<std::string> split(const std::string& s) {
 std::vector<std::string> a;size_t b=0;
 while(true){auto e=s.find(',',b);a.push_back(s.substr(b,e==std::string::npos?e:e-b));if(e==std::string::npos)break;b=e+1;}return a;
}
inline std::vector<Row> csv(const fs::path& p) {
 std::ifstream f(p);if(!f)throw std::runtime_error("input missing "+p.string());std::string s;std::getline(f,s);if(!s.empty()&&s.back()=='\r')s.pop_back();auto h=split(s);std::vector<Row>a;
 while(std::getline(f,s)){if(!s.empty()&&s.back()=='\r')s.pop_back();if(s.empty())continue;auto v=split(s);if(v.size()!=h.size())throw std::runtime_error("CSV shape");Row r;for(size_t i=0;i<h.size();++i)r[h[i]]=v[i];a.push_back(r);}return a;
}
inline double d(const Row& r,const char* k){return std::stod(r.at(k));}
inline int integer(const Row& r,const char* k){return std::stoi(r.at(k));}
struct Fixture {
 Grid2DMetadata meta;
 std::vector<Occupancy> occupancy;
 std::vector<HitProbability> hit;
 std::vector<double> posterior;
 std::vector<Vector2> wind;
 std::unique_ptr<VisibilityMap> visibility;
 HitProbabilitySettings hp;
 SimulationSettings sim;
 Fixture(const fs::path& input) {
  auto rows=csv(input/"occupancy.csv");auto& r=rows.at(0);
  meta.dimensions={integer(r,"grid_width"),integer(r,"grid_height")};meta.cellSize=d(r,"cell_size");meta.origin={float(d(r,"origin_x")),float(d(r,"origin_y"))};meta.scale=3;meta.numFreeCells=0;
  size_t n=meta.dimensions.x*meta.dimensions.y; if(rows.size()!=n)throw std::runtime_error("occupancy dimensions");
  occupancy.resize(n);hit.resize(n);wind.resize(n);posterior.resize(n);
  for(size_t i=0;i<n;++i){if(integer(rows[i],"cell_index")!=i)throw std::runtime_error("occupancy order");occupancy[i]=rows[i].at("occupancy")=="Free"?Occupancy::Free:Occupancy::Obstacle;meta.numFreeCells+=occupancy[i]==Occupancy::Free;hit[i].auxWeight=-1;hit[i].originalPropagationDirection={0,0};hit[i].setProbability(.3);}
  hp.localEstimationWindowSize=2;hp.maxUpdatesPerStop=5;hp.prior=.3;hp.kernelSigma=1.5;hp.kernelStretchConstant=1.5;hp.confidenceMeasurementWeight=1;hp.confidenceSigmaSpatial=1;
  sim.maxRegionSize=5;sim.sourceDiscriminationPower=.3;sim.refineFraction=.1;sim.deltaTime=.1;sim.noiseSTDev=.5;sim.iterationsToRecord=200;sim.minWarmupIterations=200;sim.maxWarmupIterations=500;sim.blurSigmaX=1.5;sim.blurSigmaY=1.5;
  auto w=csv(input/"wind.csv");if(w.size()!=n)throw std::runtime_error("wind dimensions");
  for(size_t i=0;i<n;++i){if(integer(w[i],"cell_index")!=i)throw std::runtime_error("wind order");wind[i]={float(d(w[i],"u")),float(d(w[i],"v"))};posterior[i]=occupancy[i]==Occupancy::Free?1./meta.numFreeCells:0.;}
  visibility=std::make_unique<VisibilityMap>(meta.dimensions.x,meta.dimensions.y,5);auto grid=hitGrid();
  for(int x=0;x<meta.dimensions.x;++x)for(int y=0;y<meta.dimensions.y;++y){Vector2Int ij(x,y);std::vector<Vector2Int> visible;
   if(grid.freeAt(x,y))for(int j=std::max(0,y-5);j<=std::min(meta.dimensions.y-1,y+5);++j)for(int i=std::max(0,x-5);i<=std::min(meta.dimensions.x-1,x+5);++i){Vector2Int z(i,j);if(z==ij||GridUtils::PathFree(meta,occupancy,meta.indicesToCoordinates(ij),meta.indicesToCoordinates(z)))visible.push_back(z);}
   visibility->emplace(ij,visible);
  }
 }
 Grid2D<HitProbability> hitGrid(){return Grid2D<HitProbability>(hit,occupancy,meta);}
 void measurement(bool detected,double direction,double speed,Vector2Int ij){auto grid=hitGrid();PMFSLib::EstimateHitProbabilities(grid,*visibility,hp,detected,direction,speed,ij);}
 template<class T=Simulations> std::unique_ptr<T> simulation() {
  auto p=std::make_unique<T>(hitGrid(),Grid2D<double>(posterior,occupancy,meta),Grid2D<Vector2>(wind,occupancy,meta),sim);
  std::vector<std::vector<uint8_t>> map(meta.dimensions.x,std::vector<uint8_t>(meta.dimensions.y));
  for(int x=0;x<meta.dimensions.x;++x)for(int y=0;y<meta.dimensions.y;++y)map[x][y]=hitGrid().freeAt(x,y)?1:0;
  p->initializeMap(map);p->visibilityMap=visibility.get();p->varianceOfHitProb.resize(hit.size());return p;
 }
 void verifyTree(const Simulations& p) {
  std::vector<int> cover(hit.size(),0);
  if(p.QTleaves.size()<2)throw std::runtime_error("candidate forest too small");
  for(const auto& n:p.QTleaves){
   if(n.value!=1||n.size.x<1||n.size.y<1)throw std::runtime_error("invalid coarse free leaf");
   for(int j=n.origin.y;j<n.origin.y+n.size.y;++j)for(int i=n.origin.x;i<n.origin.x+n.size.x;++i){
    if(i<0||j<0||i>=meta.dimensions.x||j>=meta.dimensions.y||!hitGrid().freeAt(i,j)||++cover[meta.indexOf({i,j})]!=1)throw std::runtime_error("candidate forest overlap or obstacle");
   }
  }
  for(size_t i=0;i<cover.size();++i)if(cover[i]!=(occupancy[i]==Occupancy::Free?1:0))throw std::runtime_error("candidate forest incomplete");
 }
 void restoreCapturedTree(Simulations& p,const fs::path& native) {
  auto rows=csv(native/"coarse_tree.csv");
  p.QTleaves.clear();p.QTleaves.reserve(rows.size());
  for(const auto& r:rows){
   if(r.at("parent_id")!="ROOT"||integer(r,"has_children")||integer(r,"value")!=1)throw std::runtime_error("captured coarse tree schema");
   p.QTleaves.emplace_back(nullptr,Vector2Int{integer(r,"origin_i"),integer(r,"origin_j")},Vector2Int{integer(r,"size_i"),integer(r,"size_j")},p.quadtree->map);
   p.QTleaves.back().value=1;p.QTleaves.back().parent=nullptr;
   if(R4Audit::id(&p.QTleaves.back())!=r.at("node_id"))throw std::runtime_error("captured leaf identity");
  }
  verifyTree(p);
  for(auto& column:p.mapSegmentation)std::fill(column.begin(),column.end(),nullptr);
  for(auto& n:p.QTleaves)for(int j=n.origin.y;j<n.origin.y+n.size.y;++j)for(int i=n.origin.x;i<n.origin.x+n.size.x;++i)p.mapSegmentation[i][j]=&n;
 }
 void dumpHit(const fs::path& path) {
  std::ofstream f(path);f<<std::setprecision(17)<<"cell_index,log_odds,confidence,omega,aux_weight,distance_from_robot,propagation_x,propagation_y,probability\n";
  for(size_t i=0;i<hit.size();++i){auto& h=hit[i];f<<i<<","<<h.logOdds<<","<<h.confidence<<","<<h.omega<<","<<h.auxWeight<<","<<h.distanceFromRobot<<","<<h.originalPropagationDirection.x<<","<<h.originalPropagationDirection.y<<","<<h.probability()<<"\n";}
 }
 void loadHit(const fs::path& path) {
  auto r=csv(path);if(r.size()!=hit.size())throw std::runtime_error("hit shape");
  for(size_t i=0;i<hit.size();++i){auto& h=hit[i];h.logOdds=d(r[i],"log_odds");h.confidence=d(r[i],"confidence");h.omega=d(r[i],"omega");h.auxWeight=d(r[i],"aux_weight");h.distanceFromRobot=d(r[i],"distance_from_robot");h.originalPropagationDirection={float(d(r[i],"propagation_x")),float(d(r[i],"propagation_y"))};}
 }
 void dumpPosterior(const fs::path& dir) {
  R4Audit::binary(dir/"posterior.f64",posterior);std::ofstream f(dir/"posterior.csv");f<<std::setprecision(17)<<"cell_index,probability\n";
  for(size_t i=0;i<posterior.size();++i)f<<i<<","<<posterior[i]<<"\n";
 }
};
}
