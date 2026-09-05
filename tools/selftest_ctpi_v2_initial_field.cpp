#include "../ros2_package/src/gsl_server/algorithms/PMFS/CTPIOnlineCoreV2.hpp"
#include <iomanip>
#include <iostream>
using namespace GSL::ctpi_v2;

int main()
{
    constexpr int n=1200;
    constexpr double dt=.2, wind=.5, diffusion=.01, q=1.;
    const double offset=q/(wind+diffusion);
    const std::vector<double> u(3,wind),v(3,0.);
    Transport transport(3,1,1.,diffusion,std::vector<unsigned char>(3,1));
    std::vector<double> a{10,10,10},b{10-offset,10,10},zeroA(3),zeroB(3);
    Fopdt sensorA,sensorB,controlA,controlB,offsetSensor,wrongA,wrongB;
    double fieldGap=0,sensorGap=0,controlGap=0,controlError=0,expectedGap=0;
    double squaredErrorZeroA=0,squaredErrorZeroB=0,maxState=1,offsetError=0;
    for(int k=1;k<=n;++k)
    {
        transport.advance(a,u,v,dt,0,q);
        transport.advance(b,u,v,dt,1,q);
        transport.advance(zeroA,u,v,dt,0,q);
        transport.advance(zeroB,u,v,dt,1,q);
        for(size_t j=0;j<3;++j)
        {
            maxState=std::max(maxState,std::max(a[j],b[j]));
            require(a[j]>=0&&b[j]>=0,"initial-field fixture positivity");
            offsetError=std::max(offsetError,std::abs(a[j]-b[j]-(j==0?offset:0.)));
        }
        // Fixed observed cell; the complete temporal history remains ambiguous.
        fieldGap=std::max(fieldGap,std::abs(a[2]-b[2]));
        const double measured=sensorA.step(a[2],dt);
        sensorGap=std::max(sensorGap,std::abs(measured-sensorB.step(b[2],dt)));
        const double ea=measured-wrongA.step(zeroA[2],dt);
        const double eb=measured-wrongB.step(zeroB[2],dt);
        squaredErrorZeroA+=ea*ea;
        squaredErrorZeroB+=eb*eb;
        // Observability control ONLY in this numerical unit fixture.
        const size_t controlCell=k>n-30?0:2;
        const double observedDifference=controlA.step(a[controlCell],dt)-controlB.step(b[controlCell],dt);
        const double expected=offsetSensor.step(controlCell==0?offset:0.,dt);
        controlGap=std::max(controlGap,std::abs(observedDifference));
        expectedGap=std::max(expectedGap,expected);
        controlError=std::max(controlError,std::abs(observedDifference-expected));
    }
    const double tolerance=128*std::numeric_limits<double>::epsilon()*n*maxState;
    require(offsetError<tolerance&&fieldGap<tolerance&&sensorGap<tolerance,"invisible initial-field offset identity");
    require(expectedGap>0&&controlGap>tolerance&&controlError<tolerance,"observability positive control");
    std::cout<<std::setprecision(17)
      <<"{\"status\":\"INITIAL_FIELD_ALIAS_WITNESS_VERIFIED_NOT_M1_PASS\","
      <<"\"offset\":"<<offset<<",\"max_state_offset_error\":"<<offsetError
      <<",\"max_observed_field_gap\":"<<fieldGap<<",\"max_sensor_gap\":"<<sensorGap
      <<",\"control_sensor_gap\":"<<controlGap<<",\"control_expected_gap\":"<<expectedGap
      <<",\"control_linearity_error\":"<<controlError<<",\"numerical_tolerance\":"<<tolerance
      <<",\"zero_initial_model_squared_error_source_A\":"<<squaredErrorZeroA
      <<",\"zero_initial_model_squared_error_source_B\":"<<squaredErrorZeroB<<"}\n";
}
