#pragma once

namespace GSL {

class SoftPlumeEvidenceProvider {
public:
    virtual ~SoftPlumeEvidenceProvider() = default;
    virtual double plumeHitProbability() const = 0;
    virtual double plumeHitOnThreshold() const = 0;
    virtual double plumeHitOffThreshold() const = 0;
};

}  // namespace GSL
