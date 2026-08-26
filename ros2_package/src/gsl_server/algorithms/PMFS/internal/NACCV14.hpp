#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <vector>

namespace GSL::PMFS_internal::nacc_v14
{
    // Replicated causal evidence is deliberately conjunctive.  A candidate is
    // not allowed to receive a causal correction larger than either temporal
    // parity view supports.  No independence or likelihood-product claim is
    // made here.
    inline std::vector<double> replicatedLowerEnvelope(
        const std::vector<double>& evenRank,
        const std::vector<double>& oddRank)
    {
        if (evenRank.empty() || evenRank.size() != oddRank.size())
            throw std::invalid_argument("NACC V14 replicated score shape mismatch");
        std::vector<double> result(evenRank.size(), 0.0);
        for (std::size_t i = 0; i < result.size(); ++i)
        {
            if (!std::isfinite(evenRank[i]) || !std::isfinite(oddRank[i]))
                throw std::invalid_argument("NACC V14 non-finite replicated score");
            result[i] = std::min(evenRank[i], oddRank[i]);
        }
        return result;
    }

    // KL-regularized native anchoring.
    //
    // q* = argmax_q <q, r> - KL(q || p_native)
    //    = normalize(p_native * exp(r)).
    //
    // This makes the native PMFS posterior the reference measure and gives the
    // potentially misspecified causal module only a bounded exponential tilt.
    // Scores may be shifted by any common constant without changing q*.
    inline std::vector<long double> anchoredExponentialTilt(
        const std::vector<long double>& nativeProbability,
        const std::vector<double>& cellCorrection)
    {
        if (nativeProbability.empty() || nativeProbability.size() != cellCorrection.size())
            throw std::invalid_argument("NACC V14 anchored tilt shape mismatch");

        long double nativeTotal = 0.0L;
        double maxCorrection = -std::numeric_limits<double>::infinity();
        for (std::size_t i = 0; i < nativeProbability.size(); ++i)
        {
            if (!std::isfinite(static_cast<double>(nativeProbability[i])) || nativeProbability[i] < 0.0L)
                throw std::invalid_argument("NACC V14 invalid native probability");
            if (!std::isfinite(cellCorrection[i]))
                throw std::invalid_argument("NACC V14 non-finite correction");
            nativeTotal += nativeProbability[i];
            if (nativeProbability[i] > 0.0L)
                maxCorrection = std::max(maxCorrection, cellCorrection[i]);
        }
        if (!(nativeTotal > 0.0L) || !std::isfinite(static_cast<double>(nativeTotal)) ||
            !std::isfinite(maxCorrection))
            throw std::invalid_argument("NACC V14 empty native support");

        std::vector<long double> result(nativeProbability.size(), 0.0L);
        long double total = 0.0L;
        for (std::size_t i = 0; i < result.size(); ++i)
        {
            if (nativeProbability[i] <= 0.0L)
                continue;
            const long double native = nativeProbability[i] / nativeTotal;
            result[i] = native * std::exp(static_cast<long double>(cellCorrection[i] - maxCorrection));
            total += result[i];
        }
        if (!(total > 0.0L) || !std::isfinite(static_cast<double>(total)))
            throw std::runtime_error("NACC V14 anchored tilt normalization failure");
        for (long double& value : result)
            value /= total;
        return result;
    }

    inline double maximumLogOddsDistortion(const std::vector<double>& correction)
    {
        if (correction.empty())
            throw std::invalid_argument("NACC V14 empty correction");
        const auto [lo, hi] = std::minmax_element(correction.begin(), correction.end());
        if (!std::isfinite(*lo) || !std::isfinite(*hi))
            throw std::invalid_argument("NACC V14 non-finite correction range");
        return *hi - *lo;
    }
}
