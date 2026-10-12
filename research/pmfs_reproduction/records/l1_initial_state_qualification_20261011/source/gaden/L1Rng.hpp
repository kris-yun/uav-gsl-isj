#pragma once
#include <cstdint>
#include <random>
#include <array>
#include <sstream>
#include <iomanip>
#include <stdexcept>
class L1InstanceGaussian {
 std::mt19937 engine;std::array<float,1000> table;size_t index=0;
 public:
 explicit L1InstanceGaussian(uint32_t seed):engine(seed){std::uniform_real_distribution<float> u(0,1000);index=size_t(u(engine));std::normal_distribution<double> n(0,1);for(auto&v:table)v=float(n(engine));}
 float nextValue(float mean,float sd){index=(index+1)%1000;return mean+sd*table[index];}
 std::string state()const{std::ostringstream s;s<<engine<<" "<<index<<" ";s<<std::setprecision(9);for(auto v:table)s<<v<<" ";return s.str();}
 void restore(const std::string&x){std::istringstream s(x);s>>engine>>index;for(auto&v:table)s>>v;if(!s||index>=1000)throw std::runtime_error("RNG_STATE_BAD");}
};
