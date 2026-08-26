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

    std::cout << "RCEC_V13_CORE=PASS\n";
    return 0;
}
