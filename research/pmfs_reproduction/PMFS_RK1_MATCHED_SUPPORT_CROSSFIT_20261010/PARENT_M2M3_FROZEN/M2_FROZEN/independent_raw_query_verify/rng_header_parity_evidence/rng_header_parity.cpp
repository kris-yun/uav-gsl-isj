// Header-only default-seed draw parity; no GADEN Simulation/ROS execution.
#include <gaden/internal/MathUtils.hpp>
#include <iostream>
#include <iomanip>
#include <cmath>
int main(){
 std::cout<<std::setprecision(17);
 constexpr float pi_cubed=M_PI*M_PI*M_PI;
 std::cout<<"TYPE_SQRT_FLOAT="<<sizeof(decltype(sqrt(float(8*pi_cubed))))<<"\n";
 std::cout<<"TYPE_EXP_FLOAT="<<sizeof(decltype(exp(float(-.3))))<<"\n";
 std::cout<<"PI_CUBED="<<pi_cubed<<"\n";
 for(int i=0;i<100;i++){
  float u=gaden::uniformRandom(-2.f,3.f);
  float g=gaden::GaussianRandom(.5f,float(.7f+.1f*(i%3)));
  std::cout<<"draw,"<<i<<','<<u<<','<<g<<'\n';
 }
 gaden::PrecalculatedGaussian<1000> cache;
 for(int i=0;i<64;i++)std::cout<<"cache,"<<i<<','<<cache.nextValue(.3f,.2f)<<'\n';
}
