#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <utility>
#include <vector>

namespace GSL::PMFS_internal::TNQC
{
    struct Score
    {
        bool valid = false;
        std::size_t supportCount = 0;
        std::size_t edgeCount = 0;
        double effectiveSupport = 0.0;
        double canonicalCosine = 0.0;
        double localOrderAgreement = 0.0;
        double combinedEffect = 0.0;
        double standardizedEvidence = 0.0;
    };

    inline double safeLogit(double probability, double eps = 1e-6)
    {
        const double p = std::clamp(probability, eps, 1.0 - eps);
        return std::log(p / (1.0 - p));
    }

    inline int signum(double value)
    {
        return (value > 0.0) - (value < 0.0);
    }

    // Compare two spatial fields only after quotienting independent positive
    // affine nuisance actions in logit space. The continuous channel is a
    // confidence-weighted cosine between centered fields. The auxiliary
    // channel is the weighted agreement of local order relations and is
    // invariant to any strictly increasing pointwise sensor transform.
    inline Score score(const std::vector<double>& observedLogits,
                       const std::vector<double>& predictedLogits,
                       const std::vector<double>& weights,
                       const std::vector<unsigned char>& support,
                       const std::vector<std::pair<std::size_t, std::size_t>>& localEdges)
    {
        const std::size_t n = observedLogits.size();
        if (predictedLogits.size() != n || weights.size() != n || support.size() != n)
            throw std::invalid_argument("TNQC field vectors have inconsistent sizes");

        Score out;
        double sumW = 0.0;
        double sumW2 = 0.0;
        double meanObserved = 0.0;
        double meanPredicted = 0.0;
        for (std::size_t i = 0; i < n; ++i)
        {
            if (!support[i] || !(weights[i] > 0.0) || !std::isfinite(weights[i]) ||
                !std::isfinite(observedLogits[i]) || !std::isfinite(predictedLogits[i]))
                continue;
            const double w = weights[i];
            sumW += w;
            sumW2 += w * w;
            meanObserved += w * observedLogits[i];
            meanPredicted += w * predictedLogits[i];
            ++out.supportCount;
        }
        if (out.supportCount < 4 || !(sumW > 0.0) || !(sumW2 > 0.0))
            return out;

        meanObserved /= sumW;
        meanPredicted /= sumW;
        double cross = 0.0;
        double observedNorm2 = 0.0;
        double predictedNorm2 = 0.0;
        for (std::size_t i = 0; i < n; ++i)
        {
            if (!support[i] || !(weights[i] > 0.0) || !std::isfinite(weights[i]) ||
                !std::isfinite(observedLogits[i]) || !std::isfinite(predictedLogits[i]))
                continue;
            const double xo = observedLogits[i] - meanObserved;
            const double xp = predictedLogits[i] - meanPredicted;
            const double w = weights[i];
            cross += w * xo * xp;
            observedNorm2 += w * xo * xo;
            predictedNorm2 += w * xp * xp;
        }
        if (!(observedNorm2 > 1e-18) || !(predictedNorm2 > 1e-18))
            return out;

        out.canonicalCosine = std::clamp(
            cross / std::sqrt(observedNorm2 * predictedNorm2), -1.0, 1.0);
        out.effectiveSupport = (sumW * sumW) / sumW2;

        double signedAgreement = 0.0;
        double edgeWeightSum = 0.0;
        for (const auto& edge : localEdges)
        {
            const std::size_t a = edge.first;
            const std::size_t b = edge.second;
            if (a >= n || b >= n || !support[a] || !support[b])
                continue;
            const double wa = weights[a];
            const double wb = weights[b];
            if (!(wa > 0.0) || !(wb > 0.0) || !std::isfinite(wa) || !std::isfinite(wb))
                continue;
            const int so = signum(observedLogits[a] - observedLogits[b]);
            const int sp = signum(predictedLogits[a] - predictedLogits[b]);
            if (so == 0 || sp == 0)
                continue;
            const double w = std::min(wa, wb);
            signedAgreement += w * static_cast<double>(so * sp);
            edgeWeightSum += w;
            ++out.edgeCount;
        }

        if (edgeWeightSum > 0.0)
            out.localOrderAgreement = std::clamp(signedAgreement / edgeWeightSum, -1.0, 1.0);

        // Equal-weight fusion deliberately has no fitted parameter.
        //
        // Do NOT multiply this effect by sqrt(effectiveSupport): PMFS hit-map
        // cells are spatially smoothed/correlated and therefore are not
        // independent observations.  Treating cell count as an iid sample
        // size would create pseudo-replication and can make a quotient score
        // overwhelm the native likelihood.  Confidence still enters through
        // the weighted means/cosine and local-edge weights; effectiveSupport
        // is retained as a diagnostic.  The online likelihood modifier is
        // consequently bounded to exp([-1,1]).
        out.combinedEffect = out.edgeCount >= 2
            ? 0.5 * (out.canonicalCosine + out.localOrderAgreement)
            : out.canonicalCosine;
        out.standardizedEvidence = out.combinedEffect;
        out.valid = std::isfinite(out.standardizedEvidence);
        return out;
    }
} // namespace GSL::PMFS_internal::TNQC
