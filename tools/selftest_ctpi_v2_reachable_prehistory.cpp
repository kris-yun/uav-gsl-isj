#include "../ros2_package/src/gsl_server/algorithms/PMFS/CTPIOnlineCoreV2.hpp"
#include <iomanip>
#include <iostream>
using namespace GSL::ctpi_v2;
int main()
{
    constexpr double dt=.2,q=1.,u=.5,D=.01;
    const double delta=q/(u+D);
    Transport transport(3,1,1.,D,{1,1,1});
    std::vector<double> a(3,0.),b(3,0.),wind(3,u),v(3,0.);
    const auto preA=transport.advance(a,wind,v,dt,0,delta/dt);
    const auto preB=transport.advance(b,wind,v,dt,1,0.);
    require(preA.substeps==1 && preB.substeps==1,"construction uses one substep");
    require(a[0]==delta && a[1]==0 && a[2]==0 && b==std::vector<double>(3,0.),"generated prehistory states");
    Fopdt sensorA,sensorB,controlA,controlB;
    double stateGap=0,observedGap=0,sensorGap=0,controlGap=0,maxState=1;
    for(int step=1;step<=1200;++step)
    {
        transport.advance(a,wind,v,dt,0,q);
        transport.advance(b,wind,v,dt,1,q);
        for(size_t i=0;i<3;++i)
        {
            stateGap=std::max(stateGap,std::abs(a[i]-b[i]-(i==0?delta:0.)));
            maxState=std::max({maxState,a[i],b[i]});
        }
        const size_t location=1+step%2;
        observedGap=std::max(observedGap,std::abs(a[location]-b[location]));
        sensorGap=std::max(sensorGap,std::abs(sensorA.step(a[location],dt)-sensorB.step(b[location],dt)));
        const size_t controlLocation=step>1170?0:location;
        controlGap=std::max(controlGap,std::abs(controlA.step(a[controlLocation],dt)-controlB.step(b[controlLocation],dt)));
    }
    const double tolerance=128*std::numeric_limits<double>::epsilon()*1200*maxState;
    require(stateGap<tolerance&&observedGap<tolerance&&sensorGap<tolerance,"reachable-history alias");
    require(controlGap>tolerance,"observability positive control");
    std::cout<<std::setprecision(17)<<"{\"status\":\"REACHABLE_PREHISTORY_CONDITIONAL_ALIAS_NOT_FULL_LAW_EQUIVALENCE\","
      <<"\"prehistory_rate_A\":"<<delta/dt<<",\"prehistory_rate_B\":0,\"future_rate_both\":1,"
      <<"\"initial_injected_mass_A\":"<<preA.injectedSum<<",\"initial_injected_mass_B\":"<<preB.injectedSum
      <<",\"state_offset_error\":"<<stateGap<<",\"observed_field_gap\":"<<observedGap
      <<",\"sensor_gap\":"<<sensorGap<<",\"positive_control_gap\":"<<controlGap
      <<",\"numeric_tolerance\":"<<tolerance<<"}\n";
}
