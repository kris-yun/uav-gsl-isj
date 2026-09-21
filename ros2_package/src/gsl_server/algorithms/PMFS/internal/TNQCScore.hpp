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
        // Candidate-local provisional evidence.  The final online TNQC
        // evidence is obtained only after applying the candidate-bank
        // concordance gate below.
        double combinedEffect = 0.0;
        double standardizedEvidence = 0.0;
    };

    struct BankGate
    {
        bool valid = false;
        // Informative pairs: main affine ordering exists and the local-order
        // channel has enough support and is non-tied.
        std::size_t pairCount = 0;
        double pairWeight = 0.0;
        // Reference pairs: all non-tied affine-order pairs among valid main
        // quotient candidates. Unsupported/tied local-order pairs remain in
        // this reference mass and therefore act as abstentions.
        std::size_t referencePairCount = 0;
        double referencePairWeight = 0.0;
        double informativeCoverage = 0.0;
        // Conditional concordance on informative pairs.
        double concordance = 0.0;
        // Actual shared evidence strength. This equals
        // max(0, concordance) * informativeCoverage.
        double strength = 0.0;
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
    // invariant to any strictly increasing pointwise transform of the fields.
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

        // q_aff is the exact representation quotient for independent
        // positive-affine nuisance actions on the supported logit fields.
        // q_ord is deliberately broader and is kept
        // as an independent corroboration channel.  Do not mix it into a
        // candidate score here: candidate-wise averaging can preserve each
        // candidate's sign yet still reverse the ordering between two source
        // hypotheses.  The candidate-bank gate below fixes that failure mode.
        //
        // Do NOT multiply by sqrt(effectiveSupport): PMFS hit-map cells are
        // spatially smoothed/correlated and are not iid observations.
        out.combinedEffect = out.canonicalCosine;
        out.standardizedEvidence = out.canonicalCosine;
        out.valid = std::isfinite(out.standardizedEvidence);
        return out;
    }

    // Candidate-bank quotient-channel concordance gate.
    //
    // Compare candidate orderings induced by the exact affine quotient and
    // by the broader local-order quotient.  The gate is one shared,
    // non-negative scalar for the entire candidate bank:
    //
    // Let W_main be the hypothesis-pair measure over all valid pairs whose
    // affine quotient has a non-tied ordering. Let W_info be the subset for
    // which local order also has sufficient support and a non-tied ordering.
    //
    //   C_cond = [sum_info m_i m_j sign(a_i-a_j) sign(o_i-o_j)] / W_info
    //   rho    = W_info / W_main
    //   g      = max(0, C_cond) * rho
    //          = max(0, signed_info / W_main)
    //   e_i    = g a_i
    //
    // Thus a local-order tie or lack of local-order support is a real
    // abstention: it contributes zero signed evidence but remains in the
    // reference main-order mass, so sparse corroboration cannot normalize
    // itself back to unit strength.
    //
    // m_i is the hypothesis measure represented by candidate i. Passing an
    // empty vector uses m_i=1. In PMFS V5, terminal leaf m_i is its covered
    // free-cell count. This remains exactly equivalent to cell-expanding the
    // leaf bank for both reference and informative pair masses.
    //
    // Because the same g >= 0 multiplies every affine score, the local-order
    // channel can attenuate/abstain but can never reverse the affine ranking.
    // Ties in either channel are ignored.  No source truth, candidate rank,
    // fitted coefficient, or threshold is used.
    inline BankGate candidateOrderConcordance(
        const std::vector<Score>& scores,
        const std::vector<double>& hypothesisMeasure = {})
    {
        if (!hypothesisMeasure.empty() && hypothesisMeasure.size() != scores.size())
            throw std::invalid_argument(
                "TNQC hypothesis measure must be empty or match score count");

        BankGate out;
        double signedPairs = 0.0;
        const auto measureAt = [&hypothesisMeasure](std::size_t i)
        {
            const double m = hypothesisMeasure.empty() ? 1.0 : hypothesisMeasure[i];
            if (!(m > 0.0) || !std::isfinite(m))
                throw std::invalid_argument(
                    "TNQC hypothesis measure must be finite and positive");
            return m;
        };

        for (std::size_t i = 0; i < scores.size(); ++i)
        {
            if (!scores[i].valid)
                continue;
            const double mi = measureAt(i);
            for (std::size_t j = i + 1; j < scores.size(); ++j)
            {
                if (!scores[j].valid)
                    continue;

                const int sa = signum(
                    scores[i].canonicalCosine - scores[j].canonicalCosine);
                if (sa == 0)
                    continue;

                const double pairWeight = mi * measureAt(j);
                out.referencePairWeight += pairWeight;
                ++out.referencePairCount;

                // The main quotient orders this pair, but local order cannot
                // corroborate it without support on both candidates. Keep
                // the pair in the reference mass and contribute zero.
                if (scores[i].edgeCount < 2 || scores[j].edgeCount < 2)
                    continue;

                const int so = signum(
                    scores[i].localOrderAgreement -
                    scores[j].localOrderAgreement);
                if (so == 0)
                    continue;

                signedPairs += pairWeight * static_cast<double>(sa * so);
                out.pairWeight += pairWeight;
                ++out.pairCount;
            }
        }

        if (!(out.referencePairWeight > 0.0))
            return out;

        out.informativeCoverage = std::clamp(
            out.pairWeight / out.referencePairWeight, 0.0, 1.0);
        if (out.pairWeight > 0.0)
            out.concordance = std::clamp(
                signedPairs / out.pairWeight, -1.0, 1.0);
        else
            out.concordance = 0.0;

        const double signedPerReference =
            signedPairs / out.referencePairWeight;
        out.strength = std::max(0.0, signedPerReference);
        out.valid = std::isfinite(out.strength);
        return out;
    }

    inline double bankEvidence(const Score& score, const BankGate& gate)
    {
        if (!score.valid || !gate.valid)
            return 0.0;
        return std::clamp(gate.strength * score.canonicalCosine, -1.0, 1.0);
    }
} // namespace GSL::PMFS_internal::TNQC
