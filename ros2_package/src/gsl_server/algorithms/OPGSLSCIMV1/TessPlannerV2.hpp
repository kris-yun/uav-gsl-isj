#pragma once
#include "TessCoreV2.hpp"
#include <limits>
namespace tessv2 {
struct Point2{double x,y;};
struct ActionMeta{int id;bool hard_valid;double duration;int revisit;double future_tau;double future_log_variance;std::vector<double> valid_probability;};
struct Scenario{std::vector<std::vector<double>> history;std::vector<std::vector<double>> future;std::vector<double> source_weight;std::vector<std::vector<bool>> support;};
struct ActionScore{int id;double robust_gain;bool supported;std::vector<double> scenario_gain;};
inline double d2(Point2 a,Point2 b){double x=a.x-b.x,y=a.y-b.y;return x*x+y*y;}
inline ActionScore evaluate(const std::vector<Scenario>&sc,const std::vector<Point2>&xy,int anchor,const std::vector<int>&comp,const std::vector<double>&tau,const std::vector<double>&w,const ActionMeta&a,bool drift=false){
 ActionScore o{a.id,std::numeric_limits<double>::infinity(),true,{}}; for(size_t h=0;h<sc.size();++h){for(int j:comp)if(!sc[h].support[a.id][anchor]||!sc[h].support[a.id][j])return {a.id,-std::numeric_limits<double>::infinity(),false,{}};double sum=0;for(int j:comp)sum+=std::max(0.,sc[h].source_weight[j]);if(!(sum>0))sum=comp.size();double g=0;for(int j:comp){double cw=std::max(0.,sc[h].source_weight[j]);cw=cw>0?cw/sum:1./sum;auto p=pairProfile(sc[h].history[anchor],sc[h].history[j],tau,w,drift);double fd=sc[h].future[a.id][anchor]-sc[h].future[a.id][j];auto inc=exactIncrement(p,fd,a.future_tau,a.future_log_variance);g+=cw*d2(xy[anchor],xy[j])*pairErrorReduction(p.objective,inc.deltaD);}double pv=a.valid_probability.empty()?1.:a.valid_probability[h];g*=pv;o.scenario_gain.push_back(g);o.robust_gain=std::min(o.robust_gain,g);}return o;}
inline ActionScore select(const std::vector<ActionScore>&s,const std::vector<ActionMeta>&a,double tol=1e-12){ActionScore b{-1,-std::numeric_limits<double>::infinity(),false,{}};for(auto&r:s){auto&m=a.at(r.id);if(!m.hard_valid||!r.supported)continue;if(b.id<0||r.robust_gain>b.robust_gain+tol)b=r;else if(std::abs(r.robust_gain-b.robust_gain)<=tol){auto&bm=a.at(b.id);if(m.duration<bm.duration-tol||(std::abs(m.duration-bm.duration)<=tol&&(m.revisit<bm.revisit||(m.revisit==bm.revisit&&m.id<bm.id))))b=r;}}if(b.id<0)throw std::runtime_error("no action");return b;}
}
