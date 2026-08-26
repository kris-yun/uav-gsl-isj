#include <gsl_server/algorithms/PMFS/internal/CTTTransportTrace.hpp>

#include <cassert>
#include <cmath>
#include <cstdint>
#include <stdexcept>

using GSL::PMFS_internal::ctt_v13::TransportTrace;

int main()
{
    TransportTrace trace;
    trace.reset(4, 70);
    trace.setActiveFilamentCount(0, 5);
    trace.setActiveFilamentCount(1, 9);
    trace.markOccupied(0, 0);
    trace.markOccupied(0, 0); // repeated filaments do not change binary occupancy
    trace.markOccupied(1, 65);
    trace.markOccupied(3, 0);
    trace.validate();

    assert(trace.occupied(0, 0));
    assert(!trace.occupied(1, 0));
    assert(trace.occupied(1, 65));
    assert(trace.firstHitBins[0] == 0);
    assert(trace.firstHitBins[65] == 1);
    assert(trace.firstHitBins[69] == -1);

    const auto frequencies = trace.reconstructFrequencies();
    assert(std::abs(frequencies[0] - 0.5F) < 1.0e-7F);
    assert(std::abs(frequencies[65] - 0.25F) < 1.0e-7F);
    assert(frequencies[69] == 0.0F);

    TransportTrace corrupted = trace;
    corrupted.firstHitBins[0] = 2;
    bool rejected = false;
    try
    {
        corrupted.validate();
    }
    catch (const std::runtime_error&)
    {
        rejected = true;
    }
    assert(rejected);
    return 0;
}

