#pragma once

// TESS-V4 keeps the validated variable-projection and exact rank-one
// increment mathematics from V3, and adds the physical valid-block tail
// probability used by the closed online planner.
#include "TessCoreV3.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace tessv4 {

using tessv3::BlockConfig;
using tessv3::Increment;
using tessv3::LogBlock;
using tessv3::ProfileResult;
using tessv3::ScenarioProfile;
using tessv3::TimeNormalization;
using tessv3::candidateProfile;
using tessv3::entropy;
using tessv3::exactIncrement;
using tessv3::modelAverageSourceWeights;
using tessv3::normalCdf;
using tessv3::normalizeTimes;
using tessv3::pairError;
using tessv3::pairErrorReduction;
using tessv3::pairProfile;
using tessv3::profileScenario;
using tessv3::weightedProfile;

// If log C ~ N(mu_log, total_log_variance), this is
// P(C >= raw_threshold).  The same total variance must be used by the
// exact source-separation increment and this validity probability.
inline double validBlockProbability(double mu_log,
                                    double total_log_variance,
                                    double raw_threshold) {
    if (!std::isfinite(mu_log) || !(raw_threshold > 0.0)) return 0.0;
    if (!(total_log_variance > 0.0) || !std::isfinite(total_log_variance)) {
        return std::exp(mu_log) >= raw_threshold ? 1.0 : 0.0;
    }
    const double z = (mu_log - std::log(raw_threshold)) /
                     std::sqrt(total_log_variance);
    return std::clamp(normalCdf(z), 0.0, 1.0);
}

}  // namespace tessv4
