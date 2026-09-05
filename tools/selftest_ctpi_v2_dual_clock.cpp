#include "../ros2_package/src/gsl_server/algorithms/PMFS/CTPIDualClockV2.hpp"
#include <iostream>
#include <iomanip>
using namespace GSL::ctpi_v2;
void check(bool x,const char* m) { if(!x) throw std::runtime_error(m); }
template<class F> void rejects(F f) { bool caught=false; try{f();}catch(const std::invalid_argument&){caught=true;} check(caught,"rejection missing"); }
int main()
{
    // Algebraic one-cell fixture, no House data. Source rate and durations are
    // exact test constants; .5/.2 mirrors the unbound metadata hypothesis only.
    Transport transport(1,1,1.,0.,{1});
    ClockedHypothesis actual(transport,DualClock(1049,.5,.2),{0.},0);
    ClockedHypothesis referenceSameClock(transport,DualClock(1049,.2,.2),{0.},0);
    Fopdt correctSensor,wrongSensor;
    double predicted=0.,correct=0.,wrong=0.,field=0.;
    for(int i=1;i<=20;++i)
    {
        // Varied declared forcing checks time units without assuming constant strength.
        const double rate=(i%2)?1.:2.;
        field+=rate*.5;
        predicted=actual.predict(1049+i,i*.2,0.,{0.},{0.},rate,0);
        correct=correctSensor.step(field,.2);
        wrong=wrongSensor.step(field,.5);
        check(std::abs(predicted-correct)<1e-12,"sensor must use sensor clock");
        referenceSameClock.predict(1049+i,i*.2,0.,{0.},{0.},rate,0);
    }
    check(std::abs(actual.field()[0]-15.)<1e-12,"native mass integration");
    check(std::abs(referenceSameClock.field()[0]-6.)<1e-12,"single-clock contrast");
    check(std::abs(correct-wrong)>1e-3,"wrong sensor clock negative control");
    const auto before=actual.field();
    rejects([&]{actual.predict(0,4.2,0.,{0.},{0.},1.,0);});
    rejects([&]{actual.predict(1070,4.2,4.1,{0.},{0.},1.,0);});
    rejects([&]{actual.predict(1070,4.2,4.,{}, {},1.,0);});
    check(actual.field()==before,"rejected predictions must not mutate field");
    actual.predict(1070,4.2,4.,{0.},{0.},1.,0);
    check(std::abs(actual.field()[0]-15.5)<1e-12,"resume after rejected step");
    DualClock clock(1,.5,.2);
    rejects([&]{clock.preview(3,.2);});
    rejects([&]{clock.preview(2,.4);});
    rejects([&]{DualClock invalid(1,0.,.2);});
    auto changed=clock.preview(2,.2); changed.fieldDt=.2;
    rejects([&]{clock.commit(changed);});
    DualClock tiny(1,.5,1e-12);
    rejects([&]{tiny.preview(2,0.);});
    // Advection uses native elapsed time as well, not just source accumulation.
    Transport advection(3,1,1.,0.,{1,1,1});
    ClockedHypothesis shifted(advection,DualClock(0,.5,.2),{1.,0.,0.},0);
    ClockedHypothesis wrongShift(advection,DualClock(0,.2,.2),{1.,0.,0.},0);
    shifted.predict(1,.2,0.,{2.,2.,2.},{0.,0.,0.},0.,1);
    wrongShift.predict(1,.2,0.,{2.,2.,2.},{0.,0.,0.},0.,1);
    check(std::abs(shifted.field()[1]-1.)<1e-12,"native-clock displacement");
    check(std::abs(wrongShift.field()[1]-.4)<1e-12,"single-clock displacement control");
    // Equal-clock mode preserves the existing transport-plus-sensor composition.
    ClockedHypothesis equal(transport,DualClock(0,.2,.2),{2.},0);
    Fopdt equalSensor;
    std::vector<double> equalField{2.};
    for(int i=1;i<=20;++i)
    {
        transport.advance(equalField,{0.},{0.},.2,0,1.);
        const double expected=equalSensor.step(equalField[0],.2);
        check(std::abs(equal.predict(i,i*.2,0.,{0.},{0.},1.,0)-expected)<1e-12,"equal-clock core parity");
    }
    std::cout<<std::setprecision(17)<<"{\"status\":\"DUAL_CLOCK_UNIT_ONLY_PASS\",\"native_mass\":15,\"single_clock_mass\":6,\"sensor_correct\":"
             <<correct<<",\"sensor_wrong_clock\":"<<wrong<<",\"prediction\":"<<predicted<<"}\n";
}
