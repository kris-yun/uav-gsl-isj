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

    // Candidate-wise sign checks are not enough: two positive candidates can
    // still have their relative order reversed by naive 1:1 averaging.  The
    // bank gate must detect this contradiction and abstain globally.
    TNQC::Score c0;
    c0.valid = true; c0.edgeCount = 4;
    c0.canonicalCosine = 0.51; c0.localOrderAgreement = 0.01;
    TNQC::Score c1;
    c1.valid = true; c1.edgeCount = 4;
    c1.canonicalCosine = 0.50; c1.localOrderAgreement = 1.00;
    const TNQC::BankGate disagree = TNQC::candidateOrderConcordance({c0, c1});
    assert(disagree.valid);
    assert(disagree.pairCount == 1);
    assert(close(disagree.concordance, -1.0));
    assert(close(disagree.strength, 0.0));
    assert(close(TNQC::bankEvidence(c0, disagree), 0.0));
    assert(close(TNQC::bankEvidence(c1, disagree), 0.0));

    // When the two quotient channels induce the same candidate ordering, the
    // shared gate is one and the exact affine ranking is preserved exactly.
    c0.localOrderAgreement = 0.90;
    c1.localOrderAgreement = 0.20;
    const TNQC::BankGate agree = TNQC::candidateOrderConcordance({c0, c1});
    assert(agree.valid);
    assert(close(agree.concordance, 1.0));
    assert(close(agree.strength, 1.0));
    assert(TNQC::bankEvidence(c0, agree) > TNQC::bankEvidence(c1, agree));

    // With more candidates the shared non-negative strength may attenuate the
    // exact quotient but cannot invert any affine pair ordering.
    TNQC::Score c2;
    c2.valid = true; c2.edgeCount = 4;
    c2.canonicalCosine = -0.20; c2.localOrderAgreement = -0.40;
    const TNQC::BankGate mixed = TNQC::candidateOrderConcordance({c0, c1, c2});
    assert(mixed.valid);
    const double e0 = TNQC::bankEvidence(c0, mixed);
    const double e1 = TNQC::bankEvidence(c1, mixed);
    const double e2 = TNQC::bankEvidence(c2, mixed);
    assert(e0 >= e1);
    assert(e1 >= e2);

    // Hypothesis-measure weighting must equal explicit expansion to the
    // represented cell-level hypothesis bank. Duplicate copies of one leaf
    // tie with each other and therefore contribute no within-leaf pairs.
    const TNQC::BankGate weighted =
        TNQC::candidateOrderConcordance({c0, c1, c2}, {3.0, 1.0, 2.0});
    const TNQC::BankGate expanded =
        TNQC::candidateOrderConcordance({c0, c0, c0, c1, c2, c2});
    assert(weighted.valid);
    assert(expanded.valid);
    assert(close(weighted.concordance, expanded.concordance));
    assert(close(weighted.pairWeight,
                 static_cast<double>(expanded.pairCount)));

    // Fewer than four supported cells is intentionally non-identifying.
    std::vector<unsigned char> weakSupport(observed.size(), 0);
    weakSupport[0] = weakSupport[1] = weakSupport[2] = 1;
    const TNQC::Score weak =
        TNQC::score(observed, predicted, weights, weakSupport, edges);
    assert(!weak.valid);

    std::cout << "TNQC_SCORE_TEST_PASS\n";
    return 0;
}
