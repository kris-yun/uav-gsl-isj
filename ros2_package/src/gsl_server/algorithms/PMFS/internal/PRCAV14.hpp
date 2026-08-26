#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <vector>

namespace GSL::PMFS_internal::prca_v14
{
    // Replicated causal utility.  The even/odd views are deliberately treated
    // as dependent evidence views, not independent likelihood factors.  The
    // lower envelope is the finite-view maximin score: a candidate receives
    // only the support shared by both replicated views.
    inline std::vector<double> replicatedLowerEnvelope(
        const std::vector<double>& evenRank,
        const std::vector<double>& oddRank)
    {
        if (evenRank.empty() || evenRank.size() != oddRank.size())
            throw std::invalid_argument("PRCA replicated score shape mismatch");
        std::vector<double> score(evenRank.size(), 0.0);
        for (std::size_t i = 0; i < score.size(); ++i)
        {
            if (!std::isfinite(evenRank[i]) || !std::isfinite(oddRank[i]))
                throw std::invalid_argument("PRCA replicated score non-finite input");
            score[i] = std::min(evenRank[i], oddRank[i]);
        }
        return score;
    }

    // Closed-form KL-proximal exponential tilt over any finite reference
    // distribution.  It is the unique maximizer of
    //   E_q[score] - KL(q || reference)
    // on the support of reference.  No learned weight or temperature is used;
    // the causal utility is already on the frozen standard-normal rank scale.
    inline std::vector<double> proximalTilt(
        const std::vector<double>& reference,
        const std::vector<double>& score)
    {
        if (reference.empty() || reference.size() != score.size())
            throw std::invalid_argument("PRCA proximal tilt shape mismatch");

        long double referenceTotal = 0.0L;
        double maxScore = -INFINITY;
        for (std::size_t i = 0; i < reference.size(); ++i)
        {
            if (!std::isfinite(reference[i]) || reference[i] < 0.0 ||
                !std::isfinite(score[i]))
                throw std::invalid_argument("PRCA proximal tilt invalid input");
            referenceTotal += static_cast<long double>(reference[i]);
            if (reference[i] > 0.0)
                maxScore = std::max(maxScore, score[i]);
        }
        if (!(referenceTotal > 0.0L) || !std::isfinite(maxScore))
            throw std::invalid_argument("PRCA proximal tilt empty reference support");

        std::vector<long double> unnormalized(reference.size(), 0.0L);
        long double total = 0.0L;
        for (std::size_t i = 0; i < reference.size(); ++i)
        {
            if (reference[i] <= 0.0)
                continue;
            const long double p = static_cast<long double>(reference[i]) / referenceTotal;
            const long double value = p * std::exp(
                static_cast<long double>(score[i] - maxScore));
            unnormalized[i] = value;
            total += value;
        }
        if (!(total > 0.0L) || !std::isfinite(static_cast<double>(total)))
            throw std::invalid_argument("PRCA proximal tilt normalization failure");

        std::vector<double> result(reference.size(), 0.0);
        for (std::size_t i = 0; i < result.size(); ++i)
            result[i] = static_cast<double>(unnormalized[i] / total);
        return result;
    }

    inline double klDivergence(const std::vector<double>& q,
                               const std::vector<double>& p)
    {
        if (q.empty() || q.size() != p.size())
            throw std::invalid_argument("PRCA KL shape mismatch");
        long double qTotal = 0.0L;
        long double pTotal = 0.0L;
        for (std::size_t i = 0; i < q.size(); ++i)
        {
            if (!std::isfinite(q[i]) || !std::isfinite(p[i]) ||
                q[i] < 0.0 || p[i] < 0.0)
                throw std::invalid_argument("PRCA KL invalid input");
            qTotal += q[i];
            pTotal += p[i];
        }
        if (!(qTotal > 0.0L) || !(pTotal > 0.0L))
            throw std::invalid_argument("PRCA KL zero mass");

        long double kl = 0.0L;
        for (std::size_t i = 0; i < q.size(); ++i)
        {
            const long double qi = static_cast<long double>(q[i]) / qTotal;
            const long double pi = static_cast<long double>(p[i]) / pTotal;
            if (qi <= 0.0L)
                continue;
            if (!(pi > 0.0L))
                throw std::invalid_argument("PRCA KL support violation");
            kl += qi * std::log(qi / pi);
        }
        return static_cast<double>(kl);
    }
}
