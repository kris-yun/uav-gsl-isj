// ShadowModelRunner implementation

#include "ShadowModelRunner.hpp"
#include <iomanip>
#include <sstream>

namespace GSL::OPGSLV3 {

ShadowRecord ShadowModelRunner::run(const ObservationContext& observation,
                                     bool detected) const {
    ShadowRecord record;
    if (!model_) return record;

    record.model_name = model_->name();
    record.model_hash = model_->hash();

    // Predict for all candidates
    auto predictions = model_->predictBatch(candidates_, observation);

    // Compute evidence increments
    auto increments = evidence_->accumulateBatch(detected, predictions);

    record.q_per_candidate.reserve(predictions.size());
    record.increment_per_candidate.reserve(increments.size());
    double marginal = 0.0;
    // Use uniform prior for marginal (shadow doesn't know posterior)
    const double uniform_weight = 1.0 / static_cast<double>(predictions.size());
    for (std::size_t i = 0; i < predictions.size(); ++i) {
        record.q_per_candidate.push_back(predictions[i].q);
        record.increment_per_candidate.push_back(increments[i].loglik_increment);
        marginal += uniform_weight * predictions[i].q;
    }
    record.marginal_q = marginal;
    record.evidence_policy = increments.empty() ? "" : increments[0].evidence_policy;

    return record;
}

void ShadowModelRunner::openLog(const std::string& path) {
    log_stream_.open(path);
    if (log_stream_.is_open()) {
        log_stream_ << std::fixed << std::setprecision(17);
        log_stream_ << "model_name,model_hash,evidence_policy,candidate_id,q,loglik_increment\n";
    }
}

void ShadowModelRunner::closeLog() {
    if (log_stream_.is_open()) log_stream_.close();
}

}  // namespace GSL::OPGSLV3
