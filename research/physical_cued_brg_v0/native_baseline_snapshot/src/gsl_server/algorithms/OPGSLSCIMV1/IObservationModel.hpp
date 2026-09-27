#pragma once
// OPGSL Observation Layer — IObservationModel interface
// R0: zero-behaviour-change refactoring of M1.
//
// Design contract:
//   - predict() returns a probability q in (0,1) for a single (source, observation) pair.
//   - The result carries the model name and a stable hash for trace provenance.
//   - Implementations must be stateless w.r.t. the posterior; they encode physics, not belief.
//   - Thread-safety: predict() must be const and reentrant.

#include <string>
#include <vector>

namespace GSL::OPGSLV3 {

struct SourcePoint;
struct ObservationContext;

struct ObservationPrediction {
    double q = 0.0;               // P(detection | source, observation), clipped to (eps, 1-eps)
    std::string model_name;       // e.g. "LegacyM1", "M1_R"
    std::string model_hash;       // stable content hash for trace provenance
};

class IObservationModel {
public:
    virtual ~IObservationModel() = default;

    // Predict hit probability for one candidate source under current observation.
    virtual ObservationPrediction predict(const SourcePoint& source,
                                          const ObservationContext& observation) const = 0;

    // Batch predict for all candidates. Default loops predict(); override for vectorised models.
    virtual std::vector<ObservationPrediction> predictBatch(
        const std::vector<SourcePoint>& sources,
        const ObservationContext& observation) const {
        std::vector<ObservationPrediction> results;
        results.reserve(sources.size());
        for (const auto& s : sources) {
            results.push_back(predict(s, observation));
        }
        return results;
    }

    virtual std::string name() const = 0;
    virtual std::string hash() const = 0;
};

}  // namespace GSL::OPGSLV3
