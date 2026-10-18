#include "PMFSResponseOperatorPrototype.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace pmfs_a_prime_prototype;
int main() {
    NativeHitObservation h{{0.5,0.7,0.0},{1.0,0.5,0.0},{1,1,0}};
    auto v=nativeO24Score(h,{0.2f,0.7f,200.0f});
    assert(std::abs(v-(1.-0.2*std::abs(0.5f-static_cast<double>(0.2f))))<1e-7);
    // Existing native obstacle cell keeps raw count 200 and is ignored.
    PhysicalProvenance good{"toy","measured_or_estimated","mg/s",
        "calibrated_linear_ppm","world_s","toy_solver","toy_calibration"};
    PpmObservation obs{{"r0","r1","r2"},{2.,0.5,0.},{0.1,0.1,0.1}};
    PpmCandidate right{{"r0","r1","r2"},{2.,0.5,0.},"source_a"};
    PpmCandidate wrong{{"r0","r1","r2"},{0.,1.,2.},"source_b"};
    const auto a=scoreMatchedPpm(obs,right,good);
    const auto b=scoreMatchedPpm(obs,wrong,good);
    assert(std::abs(a.best_positive_release-1.)<1e-12);
    assert(a.log_likelihood_without_shared_normalizing_constant>b.log_likelihood_without_shared_normalizing_constant);
    try {auto bad=right;bad.window_ids[0]="MISMATCH";scoreMatchedPpm(obs,bad,good);return 2;}
    catch(const std::invalid_argument&){}
    try {auto bad=good;bad.wind_input="oracle_truth";scoreMatchedPpm(obs,right,bad);return 3;}
    catch(const std::invalid_argument&){}
    std::cout<<"PASS isolated O24 hit scoring + matched ppm profile + rejection gates (synthetic)\n";
}
