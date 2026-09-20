#include <cassert>
#include <cmath>
#include <iostream>
#include <utility>
#include <vector>

#include "gsl_server/algorithms/PMFS/internal/TNQCScore.hpp"

namespace TNQC = GSL::PMFS_internal::TNQC;

namespace
{
    bool close(double a, double b, double tol = 1e-12)
    {
        return std::abs(a - b) <= tol;
    }

    std::vector<double> affine(const std::vector<double>& x, double a, double b)
    {
        std::vector<double> out;
        out.reserve(x.size());
        for (double v : x)
            out.push_back(a * v + b);
        return out;
    }

    std::vector<double> monotoneCubic(const std::vector<double>& x)
    {
        std::vector<double> out;
        out.reserve(x.size());
        for (double v : x)
            out.push_back(v * v * v + 0.25 * v);
        return out;
    }
}

int main()
{
    const std::vector<double> observed{-1.4, -0.9, -0.1, 0.35, 1.1, 1.9};
    const std::vector<double> predicted{-1.2, -0.75, 0.05, 0.45, 1.0, 2.1};
    const std::vector<double> weights{1.0, 0.8, 1.3, 0.9, 1.1, 0.7};
    const std::vector<unsigned char> support(observed.size(), 1);
    const std::vector<std::pair<std::size_t, std::size_t>> edges{
        {0,1}, {1,2}, {2,3}, {3,4}, {4,5}, {0,2}, {2,5}};

    const TNQC::Score base = TNQC::score(observed, predicted, weights, support, edges);
    assert(base.valid);
    assert(base.supportCount == observed.size());
    assert(base.edgeCount == edges.size());
    assert(base.canonicalCosine > 0.98);
    assert(base.localOrderAgreement > 0.99);
    assert(base.standardizedEvidence > 0.0);

    // Exact quotient property used by TNQC: independent positive affine
    // transforms of the observed and predicted logit fields must not alter
    // centered cosine or local ordering.
    const auto observedAffine = affine(observed, 3.7, 11.0);
    const auto predictedAffine = affine(predicted, 0.42, -4.5);
    const TNQC::Score affineScore =
        TNQC::score(observedAffine, predictedAffine, weights, support, edges);
    assert(affineScore.valid);
    assert(close(base.canonicalCosine, affineScore.canonicalCosine));
    assert(close(base.localOrderAgreement, affineScore.localOrderAgreement));
    assert(close(base.combinedEffect, affineScore.combinedEffect));
    assert(close(base.standardizedEvidence, affineScore.standardizedEvidence));

    // The local-order channel is deliberately stronger than affine
    // canonicalization: any strictly increasing pointwise sensor transform
    // preserves the edge ordering even though its continuous cosine may move.
    const TNQC::Score monotoneScore =
        TNQC::score(monotoneCubic(observed), monotoneCubic(predicted),
                    weights, support, edges);
    assert(monotoneScore.valid);
    assert(close(base.localOrderAgreement, monotoneScore.localOrderAgreement));
    assert(monotoneScore.localOrderAgreement > 0.99);

    // A spatially reversed candidate must produce negative evidence rather
    // than merely a smaller positive score.
    std::vector<double> reversed(predicted.rbegin(), predicted.rend());
    const TNQC::Score reverseScore =
        TNQC::score(observed, reversed, weights, support, edges);
    assert(reverseScore.valid);
    assert(reverseScore.canonicalCosine < -0.8);
    assert(reverseScore.localOrderAgreement < -0.5);
    assert(reverseScore.standardizedEvidence < 0.0);

    // Symmetry-hierarchy guard: a broader local-order relation may not
    // reverse the exact affine quotient.  This synthetic field is globally
    // anti-correlated while the selected local edges preserve order.
    const std::vector<double> guardObserved{0, 1, 2, 3, 4, 5};
    const std::vector<double> guardPredicted{0, 1, 2, -10, -11, -12};
    const std::vector<double> guardWeights(guardObserved.size(), 1.0);
    const std::vector<unsigned char> guardSupport(guardObserved.size(), 1);
    const std::vector<std::pair<std::size_t, std::size_t>> guardEdges{
        {0,1}, {1,2}};
    const TNQC::Score guarded = TNQC::score(
        guardObserved, guardPredicted, guardWeights, guardSupport, guardEdges);
    assert(guarded.valid);
    assert(guarded.canonicalCosine < -0.8);
    assert(guarded.localOrderAgreement > 0.99);
    assert(close(guarded.combinedEffect, guarded.canonicalCosine));
    assert(close(guarded.standardizedEvidence, guarded.canonicalCosine));

    // Fewer than four supported cells is intentionally non-identifying.
    std::vector<unsigned char> weakSupport(observed.size(), 0);
    weakSupport[0] = weakSupport[1] = weakSupport[2] = 1;
    const TNQC::Score weak =
        TNQC::score(observed, predicted, weights, weakSupport, edges);
    assert(!weak.valid);

    std::cout << "TNQC_SCORE_TEST_PASS\n";
    return 0;
}
