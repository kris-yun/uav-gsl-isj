#include <gsl_server/algorithms/PlumeTracking/PlumeTracking.hpp>
#include <gsl_server/algorithms/PlumeTracking/MovingStatePlumeTracking.hpp>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include "gsl_server/algorithms/SensorAwareSurgeCastPF/SoftPlumeEvidenceProvider.hpp"

namespace GSL
{
    void MovingStatePlumeTracking::OnUpdate()
    {
        PlumeTracking* plumeTracking = dynamic_cast<PlumeTracking*>(algorithm);
        if (!plumeTracking) throw std::runtime_error("MovingStatePlumeTracking type mismatch");

        bool gasHit = false;
        if (auto* soft = dynamic_cast<SoftPlumeEvidenceProvider*>(algorithm);
            soft && soft->plumeSoftEvidenceEnabled()) {
            const double probability = soft->plumeHitProbability();
            const bool previouslyFollowing = currentMovement == PTMovement::FollowPlume;
            gasHit = probability >= (previouslyFollowing
                                         ? soft->plumeHitOffThreshold()
                                         : soft->plumeHitOnThreshold());
        } else {
            gasHit = Utils::getAverageFloatCollection(
                         plumeTracking->lastConcentrationReadings.begin(),
                         plumeTracking->lastConcentrationReadings.end()) >
                     plumeTracking->thresholdGas;
        }

        bool foundGas = gasHit && (currentMovement == PTMovement::Exploration || currentMovement == PTMovement::RecoverPlume);
        bool lostGas = !gasHit && (currentMovement == PTMovement::FollowPlume);
        if (foundGas || lostGas)
            plumeTracking->stateMachine.forceResetState(plumeTracking->stopAndMeasureState.get());
    }

} // namespace GSL
