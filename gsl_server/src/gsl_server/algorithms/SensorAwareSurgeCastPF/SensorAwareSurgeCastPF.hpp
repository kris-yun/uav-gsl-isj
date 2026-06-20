#pragma once
#include "gsl_server/algorithms/PlumeTracking/SurgeCast/SurgeCast.hpp"
#include "SoftPlumeEvidenceProvider.hpp"
#include "uav_gsl/AdaptiveSurgeCast.hpp"
#include "uav_gsl/PoseHistory.hpp"
#include "uav_gsl/SensorBoutEstimator.hpp"
#include "uav_gsl/SoftEvidenceParticleFilter.hpp"
#include "uav_gsl/PosteriorContractionDeclaration.hpp"
#include "uav_gsl/TestTimeMixturePlumeLikelihood.hpp"
#include "uav_gsl/AnisotropicVisibilityRiskSampler.hpp"
#include <deque>
#include <fstream>
#include <memory>
#include <vector>
#include <limits>

namespace GSL {

class SensorAwareSurgeCastPF : public SurgeCast, public SoftPlumeEvidenceProvider {
public:
    explicit SensorAwareSurgeCastPF(rclcpp::Node::SharedPtr node) : SurgeCast(node) {}
    void Initialize() override;
    void OnUpdate() override;
    double plumeHitProbability() const override { return latest_evidence_.hit_probability; }
    double plumeHitOnThreshold() const override { return sensor_config_.hit_on_probability; }
    double plumeHitOffThreshold() const override { return sensor_config_.hit_off_probability; }
    bool plumeSoftEvidenceEnabled() const override { return use_sdbe_; }

protected:
    void declareParameters() override;
    float gasCallback(const olfaction_msgs::msg::GasSensor::SharedPtr msg) override;
    void processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection) override;
    GSLResult checkSourceFound() override;
    void saveResultsToFile(GSLResult result) override;

private:
    uav_gsl::SensorBoutEstimator::Config sensor_config_;
    uav_gsl::AdaptiveSurgeCast::Config policy_config_;
    uav_gsl::SoftEvidenceParticleFilter::Config pf_config_;
    uav_gsl::SensorBoutEstimator sensor_;
    uav_gsl::AdaptiveSurgeCast policy_;
    uav_gsl::PoseHistory pose_history_{20.0};
    std::unique_ptr<uav_gsl::SoftEvidenceParticleFilter> pf_;
    uav_gsl::SensorBoutEstimator::Evidence latest_evidence_;
    uav_gsl::SoftEvidenceParticleFilter::Estimate latest_estimate_;
    std::deque<double> recent_wind_directions_;
    double last_gas_time_s_{-1.0};
    double latest_measurement_dt_s_{0.1};
    std::size_t independent_bouts_{0};
    std::string audit_file_;
    bool use_sdbe_{true};
    bool use_iasc_{true};
    bool use_sepf_{true};
    bool last_raw_hit_{false};

    // Audit counters
    std::uint64_t raw_sample_count_{0};
    std::uint64_t raw_hit_count_{0};
    std::uint64_t sdbe_update_count_{0};
    std::uint64_t sepf_update_count_{0};
    std::uint64_t iasc_goal_count_{0};
    std::uint64_t invalid_goal_count_{0};
    std::uint64_t planning_failure_count_{0};
    std::uint64_t resampling_count_{0};
    std::uint64_t pf_degeneracy_count_{0};

    // Best estimate tracking for improved declaration
    uav_gsl::SoftEvidenceParticleFilter::Estimate best_estimate_;
    double best_cov_trace_{1e9};
    bool best_estimate_valid_{false};
    uav_gsl::Vec2 prev_estimate_{0, 0};
    bool prev_estimate_valid_{false};
    int stable_count_{0};
    int low_cov_count_{0};
    double min_dist_to_estimate_{1e9};
    int near_estimate_count_{0};
    int very_near_estimate_count_{0};
    bool gt_source_reached_{false};
    double last_check_s_{0.0};
    std::unique_ptr<uav_gsl::PosteriorContractionDeclaration> pcr_decl_;


    // V3 audit fields
    bool pf_updated_at_least_once_{false};
    std::string final_estimate_type_{"unset"};
    double time_to_first_reliable_bout_s_{std::numeric_limits<double>::quiet_NaN()};
    double last_bout_onset_s_{std::numeric_limits<double>::quiet_NaN()};
    std::vector<double> reacquisition_times_s_;

    double windConcentration() const;
    void ensureParticleFilterInitialized();
    void sendAdaptiveGoal(const uav_gsl::AdaptiveSurgeCast::Decision& decision);
    // KITE-SEPF 2026 modules
    bool use_kb_tme_{false};
    bool use_av_rise_{false};
    bool use_entropy_only_active_{false};
    uav_gsl::TestTimeMixturePlumeLikelihood kb_tme_;
    uav_gsl::TestTimeMixturePlumeLikelihood::Diagnostics last_tme_diag_;
    uav_gsl::AnisotropicVisibilityRiskSampler av_rise_;
    uav_gsl::AnisotropicVisibilityRiskSampler::Diagnostics last_av_diag_;
    double latest_wind_flow_to_rad_{0.0};

};

}  // namespace GSL
