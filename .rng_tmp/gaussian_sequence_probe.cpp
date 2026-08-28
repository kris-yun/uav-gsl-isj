#include "gaden/internal/MathUtils.hpp"
#include <iomanip>
#include <iostream>
int main(){ gaden::PrecalculatedGaussian<1000> g; std::cout<<std::setprecision(17); for(int i=0;i<20;++i) std::cout<<g.nextValue(0,1)<<"\n"; }
