#pragma once
#include "TessCoreV2.hpp"
#include <vector>
namespace tessv2 {
struct Sample{double value;};
inline LogBlock finalizeBlock(const std::vector<Sample>&s,double background,bool settle,const BlockConfig&cfg){
 if(s.empty())return {false,"NO_SAMPLES"};double mean=0;for(auto&x:s)mean+=x.value;mean/=s.size();double v=0;for(auto&x:s){double d=x.value-mean;v+=d*d;}v=s.size()>1?v/(s.size()-1):0;return makeLogBlock(mean,background,v,(int)s.size(),settle,cfg);
}
}
