#pragma once
#include <vector>
#include <string>
#include <cmath>
#include <stdexcept>
#include <numeric>
#include <cstdint>
// Pure schema bridge, no ROS lifecycle, simulator, truth labels, or navigation.
namespace C1A {
struct Grid { int width=34,height=45; double resolution=.25,x=-7.55,y=-7.88; std::string maskHash; std::vector<unsigned char> free; };
struct Packet { Grid grid; std::string frame="map",unit="ppm",epoch="fixture"; int64_t stateNs=1000,lastObservationNs=1000; std::vector<double> sourceProbability,varianceOfHitProb; };
struct Context { Grid grid; std::string epoch="fixture"; int64_t nowNs=2000,lastAppliedNs=0; };
struct PhysicsCertificate { bool qualified=false; std::string operatorHash; };
struct Fields { std::vector<double> sourceProbability,varianceOfHitProb; };
inline void validate(const Packet& p,const Context& c) {
 if(p.frame!="map"||p.unit!="ppm"||p.epoch!=c.epoch)throw std::runtime_error("frame_unit_epoch");
 if(p.stateNs>c.nowNs||p.lastObservationNs>p.stateNs||p.stateNs<c.lastAppliedNs)throw std::runtime_error("causal_clock");
 if(p.grid.width!=c.grid.width||p.grid.height!=c.grid.height||p.grid.resolution!=c.grid.resolution||p.grid.x!=c.grid.x||p.grid.y!=c.grid.y||p.grid.maskHash!=c.grid.maskHash||p.grid.free!=c.grid.free)throw std::runtime_error("geometry_mask");
 size_t n=c.grid.free.size();if(p.sourceProbability.size()!=n||p.varianceOfHitProb.size()!=n||n!=size_t(c.grid.width*c.grid.height))throw std::runtime_error("shape");
 double sum=0.;for(size_t i=0;i<n;++i){double s=p.sourceProbability[i],v=p.varianceOfHitProb[i];if(!std::isfinite(s)||!std::isfinite(v)||s<0||v<0||v>.25+1e-12)throw std::runtime_error("finite_bounds");if(!c.grid.free[i]&&(s!=0||v!=0))throw std::runtime_error("illegal_support");sum+=s;}
 if(std::abs(sum-1)>1e-12)throw std::runtime_error("normalization");
}
inline std::vector<double> candidateHitVariance(const std::vector<double>& sourceMass,const std::vector<std::vector<double>>& h) {
 if(h.empty()||h.size()!=sourceMass.size())throw std::runtime_error("candidate_shape");
 if(std::abs(std::accumulate(sourceMass.begin(),sourceMass.end(),0.)-1)>1e-12)throw std::runtime_error("candidate_mass");
 std::vector<double> mean(h[0].size(),0),var(h[0].size(),0);
 for(size_t s=0;s<h.size();++s){if(!std::isfinite(sourceMass[s])||sourceMass[s]<0||h[s].size()!=mean.size())throw std::runtime_error("candidate_mass_shape");for(size_t j=0;j<mean.size();++j){if(!std::isfinite(h[s][j])||h[s][j]<0||h[s][j]>1)throw std::runtime_error("hit_bounds");mean[j]+=sourceMass[s]*h[s][j];}}
 for(size_t s=0;s<h.size();++s)for(size_t j=0;j<mean.size();++j)var[j]+=sourceMass[s]*(h[s][j]-mean[j])*(h[s][j]-mean[j]);
 return var;
}
inline void applyProduction(const Packet& p,Context& c,Fields& f,const PhysicsCertificate& cert) {
 validate(p,c);if(!cert.qualified||cert.operatorHash.empty())throw std::runtime_error("physical_operator_not_qualified");
 f.sourceProbability=p.sourceProbability;f.varianceOfHitProb=p.varianceOfHitProb;c.lastAppliedNs=p.stateNs;
}
// Explicitly named fixture-only consumer. This never calls applyProduction/PMFS/Nav2.
inline void applyFixture(const Packet& p,Context& c,Fields& f){validate(p,c);f.sourceProbability=p.sourceProbability;f.varianceOfHitProb=p.varianceOfHitProb;c.lastAppliedNs=p.stateNs;}
}
