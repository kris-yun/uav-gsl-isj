#pragma once
// ShadowModelRunner — runs a shadow IObservationModel alongside the primary model.
// R0: The shadow NEVER modifies posterior, planner, navigation, or stopping.
// It only logs its predictions for offline comparison.

#include "IObservationModel.hpp"
#include "IEvidenceAccumulator.hpp"
#include <vector>
#include <string>
#include <fstream>
#include <memory>

namespace GSL::OPGSLV3 {

struct ShadowRecord {
    std::string model_name;
    std::string model_hash;
    std::string evidence_policy;
    std::vector<double> q_per_candidate;
    std::vector<double> increment_per_candidate;
    double marginal_q = 0.0;
};

class ShadowModelRunner {
public:
    ShadowModelRunner(std::unique_ptr<IObservationModel> model,
                      std::unique_ptr<IEvidenceAccumulator> evidence,
                      const std::vector<SourcePoint>& candidate_sources)
        : model_(std::move(model))
        , evidence_(std::move(evidence))
        , candidates_(candidate_sources) {}

    // Run shadow prediction for one cycle. Returns record for logging.
    // Does NOT modify any posterior state.
    ShadowRecord run(const ObservationContext& observation, bool detected) const;

    void openLog(const std::string& path);
    void closeLog();

    bool hasShadow() const { return model_ != nullptr; }
    const std::string& modelName() const { return model_->name(); }

private:
    std::unique_ptr<IObservationModel> model_;
    std::unique_ptr<IEvidenceAccumulator> evidence_;
    const std::vector<SourcePoint>& candidates_;
    std::ofstream log_stream_;
};

}  // namespace GSL::OPGSLV3
