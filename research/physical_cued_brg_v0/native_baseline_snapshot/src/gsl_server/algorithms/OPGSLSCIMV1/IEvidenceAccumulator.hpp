#pragma once
// OPGSL Observation Layer — IEvidenceAccumulator interface
// R0: zero-behaviour-change refactoring.
//
// The evidence accumulator converts a raw observation prediction + event outcome
// into a log-likelihood increment for each candidate source.
// This separates "what q means" from "how q updates the posterior".

#include <vector>
#include <string>

namespace GSL::OPGSLV3 {

struct SourcePoint;
struct ObservationContext;
struct ObservationPrediction;

struct EvidenceIncrement {
    double loglik_increment = 0.0;   // added to log-posterior for this candidate
    std::string evidence_policy;     // e.g. "independent_bernoulli", "power_lambda_0.5"
};

class IEvidenceAccumulator {
public:
    virtual ~IEvidenceAccumulator() = default;

    // Compute the evidence increment for one candidate given the event outcome.
    virtual EvidenceIncrement accumulate(bool detected,
                                         const ObservationPrediction& prediction) const = 0;

    // Batch version for all candidates in one cycle.
    virtual std::vector<EvidenceIncrement> accumulateBatch(
        bool detected,
        const std::vector<ObservationPrediction>& predictions) const {
        std::vector<EvidenceIncrement> results;
        results.reserve(predictions.size());
        for (const auto& p : predictions) {
            results.push_back(accumulate(detected, p));
        }
        return results;
    }

    virtual std::string name() const = 0;
};

}  // namespace GSL::OPGSLV3
