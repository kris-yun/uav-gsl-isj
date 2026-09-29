#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
namespace tessv2 {
struct BlockConfig {double min_corrected{1e-6}; double saturation{std::numeric_limits<double>::infinity()}; int min_effective_samples{3}; double log_variance_floor{1e-4};};
struct LogBlock {bool accepted{false}; std::string reason; double corrected{NAN}, log_value{NAN}, log_variance{NAN}, weight{NAN};};
inline LogBlock makeLogBlock(double mean,double background,double within_var,int n_eff,bool settle,const BlockConfig& c={}){
  if(!std::isfinite(mean)||!std::isfinite(background)||!std::isfinite(within_var))return {false,"NONFINITE"};
  if(!settle)return {false,"INVALID_SETTLE"}; if(n_eff<c.min_effective_samples)return {false,"INSUFFICIENT_SAMPLES"};
  if(mean>=c.saturation)return {false,"SATURATED"}; double x=mean-background;
  if(x<c.min_corrected)return {false,"LOW_SIGNAL",x}; if(within_var<0)return {false,"NEGATIVE_VARIANCE",x};
  double vz=std::max(within_var/std::max(n_eff,1)/(x*x),c.log_variance_floor); return {true,"ACCEPTED",x,std::log(x),vz,1.0/vz};
}
struct ProfileResult {double objective{0}; std::array<double,2> eta{0,0}; std::array<double,4> Ainv{0,0,0,0}; int dim{1};};
inline double normalCdf(double x){return .5*(1.+std::erf(x/std::sqrt(2.)));}
inline ProfileResult weightedProfile(const std::vector<double>& y,const std::vector<double>& tau,const std::vector<double>& w,bool drift){
  if(y.empty()||y.size()!=w.size()||(drift&&tau.size()!=y.size()))throw std::invalid_argument("shape");
  double a00=0,a01=0,a11=0,b0=0,b1=0; for(size_t k=0;k<y.size();++k){if(!(w[k]>0))throw std::invalid_argument("w"); double t=drift?tau[k]:0; a00+=w[k];a01+=w[k]*t;a11+=w[k]*t*t;b0+=w[k]*y[k];b1+=w[k]*t*y[k];}
  ProfileResult o;o.dim=drift?2:1;if(!drift){o.Ainv={1/a00,0,0,0};o.eta={b0/a00,0};}else{double det=a00*a11-a01*a01;if(!(det>1e-14*std::max({std::abs(a00*a11),std::abs(a01*a01),1.})))throw std::runtime_error("singular");o.Ainv={a11/det,-a01/det,-a01/det,a00/det};o.eta={(a11*b0-a01*b1)/det,(-a01*b0+a00*b1)/det};}
  for(size_t k=0;k<y.size();++k){double r=y[k]-o.eta[0]-(drift?o.eta[1]*tau[k]:0);o.objective+=w[k]*r*r;} return o;
}
inline ProfileResult pairProfile(const std::vector<double>& a,const std::vector<double>& b,const std::vector<double>& tau,const std::vector<double>& w,bool drift){if(a.size()!=b.size())throw std::invalid_argument("shape");std::vector<double>d(a.size());for(size_t i=0;i<a.size();++i)d[i]=a[i]-b[i];return weightedProfile(d,tau,w,drift);}
struct Increment {double deltaD,innovation,leverage;};
inline Increment exactIncrement(const ProfileResult&p,double fd,double future_tau,double future_log_variance){if(!(future_log_variance>0))throw std::invalid_argument("var");double wf=1/future_log_variance,b0=1,b1=p.dim==2?future_tau:0;double e=fd-b0*p.eta[0]-b1*p.eta[1];double l=b0*(p.Ainv[0]*b0+p.Ainv[1]*b1)+b1*(p.Ainv[2]*b0+p.Ainv[3]*b1);return {std::max(0.,wf*e*e/(1+wf*l)),e,l};}
inline double pairError(double D){return normalCdf(-std::sqrt(std::max(D,0.))/2.);}
inline double pairErrorReduction(double D,double dD){return std::max(0.,pairError(D)-pairError(D+std::max(dD,0.)));}
}
