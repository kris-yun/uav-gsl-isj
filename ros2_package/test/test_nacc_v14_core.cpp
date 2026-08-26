#include "gsl_server/algorithms/PMFS/internal/NACCV14.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>

using namespace GSL::PMFS_internal::nacc_v14;

int main()
{
    const std::vector<double> even{2.0, -1.0, 0.5};
    const std::vector<double> odd{1.0,  3.0, 0.2};
    const auto lower = replicatedLowerEnvelope(even, odd);
    assert(lower[0] == 1.0 && lower[1] == -1.0 && lower[2] == 0.2);

    const std::vector<long double> native{0.8L, 0.15L, 0.05L};
    const std::vector<double> zero{0.0, 0.0, 0.0};
    const auto unchanged = anchoredExponentialTilt(native, zero);
    assert(std::abs(static_cast<double>(unchanged[0] - 0.8L)) < 1e-15);
    assert(std::abs(static_cast<double>(unchanged[1] - 0.15L)) < 1e-15);
    assert(std::abs(static_cast<double>(unchanged[2] - 0.05L)) < 1e-15);

    const std::vector<double> correction{0.7, -0.2, 0.1};
    const std::vector<double> shifted{12.7, 11.8, 12.1};
    const auto q = anchoredExponentialTilt(native, correction);
    const auto qShifted = anchoredExponentialTilt(native, shifted);
    for (std::size_t i = 0; i < q.size(); ++i)
        assert(std::abs(static_cast<double>(q[i] - qShifted[i])) < 1e-14);

    // Gibbs / KL-regularized odds identity:
    // log[(q0/q1)/(p0/p1)] = r0-r1.
    const double logOddsShift = std::log(static_cast<double>(q[0] / q[1])) -
        std::log(static_cast<double>(native[0] / native[1]));
    assert(std::abs(logOddsShift - (correction[0] - correction[1])) < 1e-13);

    const double range = maximumLogOddsDistortion(correction);
    assert(std::abs(range - 0.9) < 1e-15);

    // If native odds exceed the maximum possible auxiliary odds change, the
    // auxiliary module cannot reverse that pairwise ordering.
    const std::vector<long double> protectedNative{0.99L, 0.01L};
    const std::vector<double> boundedCorrection{-1.0, 1.0};
    const auto protectedQ = anchoredExponentialTilt(protectedNative, boundedCorrection);
    assert(protectedQ[0] > protectedQ[1]);

    std::cout << "NACC_V14_REPLICATED_LOWER_ENVELOPE=PASS\n";
    std::cout << "NACC_V14_KL_ANCHORED_TILT=PASS\n";
    std::cout << "NACC_V14_ODDS_BOUND=PASS\n";
    return 0;
}
