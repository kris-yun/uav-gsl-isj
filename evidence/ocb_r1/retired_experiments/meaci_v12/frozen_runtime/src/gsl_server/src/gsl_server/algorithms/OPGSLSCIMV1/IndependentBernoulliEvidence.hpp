#pragma once
// IndependentBernoulliEvidence — wraps current hit/miss log-likelihood.
// R0: zero-behaviour-change.
//   detected=1: increment = log(q)
//   detected=0: increment = log(1-q) = log1p(-q)

#include "IEvidenceAccumulator.hpp"
#include "IObservationModel.hpp"
#include <cmath>

namespace GSL::OPGSLV3 {

class IndependentBernoulliEvidence : public IEvidenceAccumulator {
public:
    EvidenceIncrement accumulate(bool detected,
                                 const ObservationPrediction& prediction) const override {
        EvidenceIncrement inc;
        const double q = prediction.q;
        inc.loglik_increment = detected ? std::log(q) : std::log1p(-q);
        inc.evidence_policy = "independent_bernoulli";
        return inc;
    }

    std::string name() const override { return "IndependentBernoulli"; }
};

// Future: PowerBernoulliEvidence with lambda parameter for CAPP.
// Not part of R0.

}  // namespace GSL::OPGSLV3
