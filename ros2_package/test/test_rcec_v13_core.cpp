#include "gsl_server/algorithms/PMFS/internal/RCECV13.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
#include <string>
#include <vector>

using namespace GSL::PMFS_internal::rcec_v13;

int main()
{
    const std::vector<std::string> ids{"a","b","c","d"};
    const std::vector<double> values{4.0, 1.0, 3.0, 2.0};
    const auto ranks = normalRanks(values, ids);
    assert(ranks[0] > ranks[2] && ranks[2] > ranks[3] && ranks[3] > ranks[1]);

    // RCEC_V13_EXACT_TIE_RANK_V21_20260826: values that merely differ by
    // less than 1e-12 are still distinct candidate masses and must retain
    // strict rank order.  Only exact equality receives an average tie rank.
    const std::vector<std::string> tinyIds{"z0","z1","z2","z3","z4"};
    const std::vector<double> tinyMasses{0.0, 1e-15, 2e-15, 2e-15, 1.0};
    const auto tinyRanks = normalRanks(tinyMasses, tinyIds);
    assert(tinyRanks[0] < tinyRanks[1]);
    assert(tinyRanks[1] < tinyRanks[2]);
    assert(tinyRanks[2] == tinyRanks[3]);
    assert(tinyRanks[3] < tinyRanks[4]);

    // Stable IDs may order exact ties deterministically internally, but exact
    // ties must receive the same average rank regardless of ID ordering.
    const std::vector<std::string> tieIds{"b","a","c"};
    const std::vector<double> exactTies{0.25, 0.25, 0.5};
    const auto tieRanks = normalRanks(exactTies, tieIds);
    assert(tieRanks[0] == tieRanks[1]);
    assert(tieRanks[1] < tieRanks[2]);

    const std::vector<double> n{1.0, 2.0, -2.0};
    const std::vector<double> e{0.5, 3.0, -1.0};
    const std::vector<double> o{0.8, 1.5,  0.0};
    const auto c = conjunctiveConsensus(n, e, o);
    assert(c[0] == 0.5 && c[1] == 1.5 && c[2] == -2.0);

    const std::vector<std::vector<double>> h1{{1.0, 8.0}};
    const auto m1 = temporalMedian(h1);
    assert(m1[0] == 1.0 && m1[1] == 8.0);

    const std::vector<std::vector<double>> h2{{1.0, 8.0}, {3.0, 4.0}};
    const auto m2 = temporalMedian(h2);
    assert(std::abs(m2[0] - 2.0) < 1e-15 && std::abs(m2[1] - 6.0) < 1e-15);

    const std::vector<std::vector<double>> h3{{100.0, 1.0}, {2.0, 3.0}, {1.0, 2.0}};
    const auto m3 = temporalMedian(h3);
    assert(m3[0] == 2.0 && m3[1] == 2.0);

    std::cout << "RCEC_V13_RANK_CONTRACT=PASS\n";
    std::cout << "RCEC_V13_CORE=PASS\n";
    return 0;
}
