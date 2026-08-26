#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace GSL::PMFS_internal::rcec_v13
{
    inline double normalQuantile(double probability)
    {
        const double p = std::clamp(probability, 1e-12, 1.0 - 1e-12);
        constexpr double a1 = -3.969683028665376e+01;
        constexpr double a2 =  2.209460984245205e+02;
        constexpr double a3 = -2.759285104469687e+02;
        constexpr double a4 =  1.383577518672690e+02;
        constexpr double a5 = -3.066479806614716e+01;
        constexpr double a6 =  2.506628277459239e+00;
        constexpr double b1 = -5.447609879822406e+01;
        constexpr double b2 =  1.615858368580409e+02;
        constexpr double b3 = -1.556989798598866e+02;
        constexpr double b4 =  6.680131188771972e+01;
        constexpr double b5 = -1.328068155288572e+01;
        constexpr double c1 = -7.784894002430293e-03;
        constexpr double c2 = -3.223964580411365e-01;
        constexpr double c3 = -2.400758277161838e+00;
        constexpr double c4 = -2.549732539343734e+00;
        constexpr double c5 =  4.374664141464968e+00;
        constexpr double c6 =  2.938163982698783e+00;
        constexpr double d1 =  7.784695709041462e-03;
        constexpr double d2 =  3.224671290700398e-01;
        constexpr double d3 =  2.445134137142996e+00;
        constexpr double d4 =  3.754408661907416e+00;
        constexpr double low = 0.02425;
        constexpr double high = 1.0 - low;
        if (p < low)
        {
            const double q = std::sqrt(-2.0 * std::log(p));
            return (((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6) /
                   ((((d1*q+d2)*q+d3)*q+d4)*q+1.0);
        }
        if (p > high)
        {
            const double q = std::sqrt(-2.0 * std::log(1.0-p));
            return -(((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6) /
                    ((((d1*q+d2)*q+d3)*q+d4)*q+1.0);
        }
        const double q = p - 0.5;
        const double r = q * q;
        return (((((a1*r+a2)*r+a3)*r+a4)*r+a5)*r+a6)*q /
               (((((b1*r+b2)*r+b3)*r+b4)*r+b5)*r+1.0);
    }

    inline std::vector<double> normalRanks(const std::vector<double>& values,
                                           const std::vector<std::string>& stableIds)
    {
        if (values.empty() || values.size() != stableIds.size())
            throw std::invalid_argument("RCEC normalRanks shape mismatch");
        for (double value : values)
            if (!std::isfinite(value))
                throw std::invalid_argument("RCEC normalRanks non-finite input");

        std::vector<std::size_t> order(values.size());
        for (std::size_t i = 0; i < order.size(); ++i)
            order[i] = i;
        std::sort(order.begin(), order.end(), [&](std::size_t a, std::size_t b)
        {
            if (values[a] != values[b])
                return values[a] < values[b];
            return stableIds[a] < stableIds[b];
        });

        std::vector<double> result(values.size(), 0.0);
        std::size_t begin = 0;
        while (begin < order.size())
        {
            std::size_t end = begin + 1;
            // RCEC_V13_EXACT_TIE_RANK_V21_20260826.
            // Candidate masses are probabilities and can legitimately differ
            // by far less than 1e-12.  An absolute tolerance at that scale
            // collapses a large low-mass tail into a false tie and changes the
            // order statistic.  Average only genuine floating-point equality,
            // matching the offline average-rank contract.  Stable IDs provide
            // deterministic ordering of exact ties before they receive their
            // common average rank.
            while (end < order.size() &&
                   values[order[end]] == values[order[begin]])
                ++end;
            const double averageRank = 0.5 *
                (static_cast<double>(begin + 1) + static_cast<double>(end));
            const double z = normalQuantile(
                (averageRank - 0.5) / static_cast<double>(order.size()));
            for (std::size_t i = begin; i < end; ++i)
                result[order[i]] = z;
            begin = end;
        }
        return result;
    }

    inline std::vector<double> conjunctiveConsensus(const std::vector<double>& nativeRank,
                                                    const std::vector<double>& evenRank,
                                                    const std::vector<double>& oddRank)
    {
        if (nativeRank.size() != evenRank.size() || nativeRank.size() != oddRank.size() || nativeRank.empty())
            throw std::invalid_argument("RCEC consensus shape mismatch");
        std::vector<double> result(nativeRank.size());
        for (std::size_t i = 0; i < result.size(); ++i)
            result[i] = std::min({nativeRank[i], evenRank[i], oddRank[i]});
        return result;
    }

    inline double median(std::vector<double> values)
    {
        if (values.empty())
            throw std::invalid_argument("RCEC median empty");
        const std::size_t middle = values.size() / 2;
        std::nth_element(values.begin(), values.begin() + static_cast<std::ptrdiff_t>(middle), values.end());
        const double upper = values[middle];
        if ((values.size() & 1U) != 0U)
            return upper;
        const double lower = *std::max_element(values.begin(), values.begin() + static_cast<std::ptrdiff_t>(middle));
        return 0.5 * (lower + upper);
    }

    inline std::vector<double> temporalMedian(const std::vector<std::vector<double>>& history)
    {
        if (history.empty() || history.front().empty())
            throw std::invalid_argument("RCEC temporal history empty");
        const std::size_t candidates = history.front().size();
        for (const auto& snapshot : history)
            if (snapshot.size() != candidates)
                throw std::invalid_argument("RCEC temporal history shape drift");
        std::vector<double> result(candidates, 0.0);
        std::vector<double> scratch;
        scratch.reserve(history.size());
        for (std::size_t s = 0; s < candidates; ++s)
        {
            scratch.clear();
            for (const auto& snapshot : history)
                scratch.push_back(snapshot[s]);
            result[s] = median(scratch);
        }
        return result;
    }
}
