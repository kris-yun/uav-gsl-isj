#pragma once
// LegacyM1ObservationModel — wraps current hitProbability() as an IObservationModel.
// R0: zero-behaviour-change. The predict() output is bit-identical to the original.

#include "IObservationModel.hpp"
#include <cmath>
#include <algorithm>

namespace GSL::OPGSLV3 {

struct ObservationModelParameters;  // forward, defined in OPGSLScientificV31.hpp

class LegacyM1ObservationModel : public IObservationModel {
public:
    explicit LegacyM1ObservationModel(const ObservationModelParameters& params)
        : params_(params) {}

    ObservationPrediction predict(const SourcePoint& source,
                                  const ObservationContext& observation) const override;

    std::string name() const override { return "LegacyM1"; }
    std::string hash() const override;  // content hash of params_

private:
    const ObservationModelParameters& params_;
};

}  // namespace GSL::OPGSLV3
