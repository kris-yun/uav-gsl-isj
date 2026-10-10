#pragma once
#include "Audit.hpp"
#include <map>
#include <tuple>
namespace M3Audit {
inline bool wallSlide=false;
inline int phase=0,depth=0;
inline uint64_t blocked=0,slideAttempts=0,slideNonzero=0,guardHits=0,originBlocked=0,visibilityFast=0;
struct Counts {uint64_t moves=0,blocked=0,zero=0;long double displacement=0;};
inline std::map<std::tuple<int,int,int,int,int>,Counts> transitions;
inline void movement(const GSL::Vector2& p0,const GSL::Vector2& p1,GSL::Vector2Int a,GSL::Vector2Int b,uint64_t beforeBlocked) {
  auto& c=transitions[{phase,a.x,a.y,b.x,b.y}];c.moves++;c.blocked+=blocked-beforeBlocked;
  if(p0.x==p1.x&&p0.y==p1.y)c.zero++;
  double dx=double(p1.x)-p0.x,dy=double(p1.y)-p0.y;c.displacement+=std::sqrt(dx*dx+dy*dy);
}
inline void finish(const std::filesystem::path& out) {
 std::ofstream f(out/"MOVEMENT_CELL_AGGREGATES.csv");f<<std::setprecision(21)<<"phase,start_i,start_j,end_i,end_j,moves,blocked_encounters,zero_displacement,total_displacement_m\n";
 for(const auto& [k,v]:transitions){auto [p,x,y,a,b]=k;f<<p<<","<<x<<","<<y<<","<<a<<","<<b<<","<<v.moves<<","<<v.blocked<<","<<v.zero<<","<<v.displacement<<"\n";}
 std::ofstream s(out/"MOVEMENT_COUNTERS.json");s<<"{\"blocked_encounters\":"<<blocked<<",\"slide_attempts\":"<<slideAttempts<<",\"slide_nonzero_projections\":"<<slideNonzero<<",\"recursion_guard_hits\":"<<guardHits<<",\"invalid_start_cell\":"<<originBlocked<<",\"visibility_fastpath\":"<<visibilityFast<<"}";
}
}
