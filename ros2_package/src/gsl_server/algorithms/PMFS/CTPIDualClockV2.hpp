#pragma once
#include "CTPIOnlineCoreV2.hpp"

namespace GSL::ctpi_v2
{
// Explicit continuous segment clock. Native field duration is metadata, not a
// learned scale or a default 2.5 multiplier. The caller must bind its provenance.
// A replay wrap is not a valid continuous step and cannot reset sensor history.
class DualClock
{
    long long frame_;
    double sensorStamp_=0., fieldDt_, sensorDt_;
public:
    struct Step { double sensorDt, fieldDt, sensorStamp; long long nativeFrame; };
    DualClock(long long initialNativeFrame, double fieldDt, double sensorDt)
        : frame_(initialNativeFrame), fieldDt_(fieldDt), sensorDt_(sensorDt)
    {
        require(frame_>=0 && frame_<std::numeric_limits<long long>::max(),"CTPI_V2_CLOCK_ORIGIN");
        require(std::isfinite(fieldDt)&&fieldDt>0 && std::isfinite(sensorDt)&&sensorDt>0,
                "CTPI_V2_CLOCK_DURATION");
    }
    Step preview(long long nativeFrame, double sensorStamp) const
    {
        require(frame_<std::numeric_limits<long long>::max() && nativeFrame==frame_+1,
                "CTPI_V2_FIELD_GAP_OR_REPLAY_SEAM");
        require(std::isfinite(sensorStamp) && sensorStamp>sensorStamp_ && std::abs(sensorStamp-sensorStamp_-sensorDt_)<=1e-9,
                "CTPI_V2_SENSOR_CLOCK_GAP");
        return {sensorDt_,fieldDt_,sensorStamp,nativeFrame};
    }
    void commit(const Step& step)
    {
        const auto expected=preview(step.nativeFrame,step.sensorStamp);
        require(step.sensorDt==expected.sensorDt && step.fieldDt==expected.fieldDt,
                "CTPI_V2_CLOCK_STEP_ALTERED");
        frame_=step.nativeFrame; sensorStamp_=step.sensorStamp;
    }
    double sensorStamp() const { return sensorStamp_; }
};

// One conditional source/initial-field hypothesis, not an M1 posterior. New
// step-wise source rates may be supplied by a declared nuisance model; no fixed
// rate or zero initial gas field is silently assumed. Unknown native timing,
// field boundaries and complete initial state still require qualification.
class ClockedHypothesis
{
    Transport transport_;
    DualClock clock_;
    std::vector<double> field_;
    Fopdt sensor_;
    size_t source_;
public:
    ClockedHypothesis(Transport transport, DualClock clock,
                      std::vector<double> initialField, size_t source)
        : transport_(std::move(transport)),clock_(std::move(clock)),
          field_(std::move(initialField)),source_(source) {}

    double predict(long long nativeFrame, double sensorStamp, double windAvailableAt,
                   const std::vector<double>& u, const std::vector<double>& v,
                   double sourceRatePerNativeSecond, size_t sampleCell)
    {
        const auto step=clock_.preview(nativeFrame,sensorStamp);
        require(std::isfinite(windAvailableAt)&&windAvailableAt>=0&&windAvailableAt<=clock_.sensorStamp(),
                "CTPI_V2_FUTURE_WIND_INPUT");
        require(sampleCell<field_.size(),"CTPI_V2_SAMPLE_CELL");
        // Transactional: a rejected frame cannot partially advance plume or sensor.
        auto nextField=field_;
        auto nextSensor=sensor_;
        transport_.advance(nextField,u,v,step.fieldDt,source_,sourceRatePerNativeSecond);
        const double prediction=nextSensor.step(nextField[sampleCell],step.sensorDt);
        clock_.commit(step);
        field_=std::move(nextField); sensor_=std::move(nextSensor);
        return prediction;
    }
    const std::vector<double>& field() const { return field_; }
};
}
