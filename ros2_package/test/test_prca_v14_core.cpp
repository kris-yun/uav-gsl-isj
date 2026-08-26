#include "gsl_server/algorithms/PMFS/internal/PRCAV14.hpp"

#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>

using namespace GSL::PMFS_internal::prca_v14;

int main()
{
    const std::vector<double> even{1.0, -2.0, 0.5};
    const std::vector<double> odd{0.25, -1.0, 0.75};
    const auto lower = replicatedLowerEnvelope(even, odd);
    assert(lower.size() == 3);
    assert(lower[0] == 0.25 && lower[1] == -2.0 && lower[2] == 0.5);

    // Constant utility is exactly the native/reference distribution.
    const std::vector<double> p{0.7, 0.2, 0.1};
    const std::vector<double> constant{3.0, 3.0, 3.0};
    const auto unchanged = proximalTilt(p, constant);
    for (std::size_t i = 0; i < p.size(); ++i)
        assert(std::abs(unchanged[i] - p[i]) < 1e-15);

    // Reference zeros are support-preserving: causal evidence cannot invent
    // source support that native PMFS assigns exactly zero probability.
    const std::vector<double> pSupport{0.8, 0.2, 0.0};
    const std::vector<double> supportScore{-1.0, 0.0, 100.0};
    const auto supported = proximalTilt(pSupport, supportScore);
    assert(supported[2] == 0.0);
    assert(std::abs(supported[0] + supported[1] - 1.0) < 1e-15);

    // Pairwise odds obey the exact exponential-tilt identity.
    const std::vector<double> oddsBase{0.4, 0.6};
    const std::vector<double> oddsScore{0.5, -0.25};
    const auto oddsTilt = proximalTilt(oddsBase, oddsScore);
    const double observedRatio = (oddsTilt[0] / oddsTilt[1]) /
                                 (oddsBase[0] / oddsBase[1]);
    assert(std::abs(observedRatio - std::exp(0.75)) < 1e-14);

    // Adding a constant to every utility leaves the proximal solution intact.
    const std::vector<double> shiftedScore{10.5, 9.75};
    const auto shifted = proximalTilt(oddsBase, shiftedScore);
    assert(std::abs(shifted[0] - oddsTilt[0]) < 1e-15);
    assert(std::abs(shifted[1] - oddsTilt[1]) < 1e-15);

    // The KL penalty is finite and positive for a nontrivial supported update.
    const double kl = klDivergence(oddsTilt, oddsBase);
    assert(std::isfinite(kl) && kl > 0.0);

    std::cout << "PRCA_V14_CORE=PASS\n";
    std::cout << "PRCA_V14_SUPPORT_PRESERVATION=PASS\n";
    std::cout << "PRCA_V14_ODDS_IDENTITY=PASS\n";
    return 0;
}
