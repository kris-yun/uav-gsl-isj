#pragma once

#include <gsl_server/algorithms/OPGSLScientificV31/OPGSLScientificV31.hpp>
#include <gsl_server/algorithms/Common/Algorithm.hpp>
#include <gsl_server/algorithms/Common/States/MovingState.hpp>
#include <SCIMCore.hpp>
#include "TransportModel.hpp"
#include "SNOEDPlanner.hpp"
#include "TessCoreV4.hpp"
#include "TessPlannerV4.hpp"
#include "TessAdaptiveGateV42.hpp"
#include "TessPerformanceGateV43.hpp"
#include "TessBlockAccumulatorV3.hpp"
#include "TessFopdtV3.hpp"

#ifndef OPGSL_CORE_STANDALONE

#include <fstream>
#include <limits>
#include <memory>
#include <random>
#include <string>
#include <unordered_map>
#include <optional>
#include <std_msgs/msg/bool.hpp>
#include <std_srvs/srv/set_bool.hpp>

namespace GSL {

class OPGSLSCIMV1;

class MovingStateOPGSLSCIMV1 final : public MovingState {
public:
    explicit MovingStateOPGSLSCIMV1(Algorithm* algorithm);
    void chooseGoalAndMove() override;
    void OnUpdate() override;
    void requestReplan();

protected:
    void Fail() override;

private:
    OPGSLSCIMV1* scim_ = nullptr;
    bool replan_required_ = false;
    int replan_wait_ticks_ = 0;
    double active_navigation_timeout_seconds_ = 6.0;
    rclcpp::Time goal_sent_time_{0, 0, RCL_ROS_TIME};
    bool goal_timer_active_ = false;
    NavigateToPose::Goal posToGoal(double x, double y, double z) const;
};

class OPGSLSCIMV1 : public Algorithm {
    friend class MovingStateOPGSLSCIMV1;

public:
    explicit OPGSLSCIMV1(std::shared_ptr<rclcpp::Node> node);
    void Initialize() override;
    void forceSimulationTimeBudgetReached();

protected:
    void declareParameters() override;
    void processGasAndWindMeasurements(double concentration,
                                       double windSpeed,
                                       double windDirection) override;
    GSLResult checkSourceFound() override;
    void saveResultsToFile(GSLResult result) override;
    void OnUpdate() override;
    void OnCompleteNavigation(GSLResult result, State* previousState) override;
    void onGetMap(const OccupancyGrid::SharedPtr msg) override;

private:
    struct RuntimeConfig {
        bool scientific_mode = true;
        bool enable_ncl = false;
        int grid_nx = 30;
        int grid_ny = 30;
        int grid_nz = 1;
        double source_z_min = 0.0;
        double source_z_max = 0.0;
        double nominal_flight_height = 0.3;
        double min_flight_height = 0.3;
        double max_flight_height = 0.3;
        int angular_samples = 16;
        int radial_samples = 2;
        double min_action_radius = 0.6;
        double max_action_radius = 1.8;
        int max_steps = 300;
        int seed = 0;
        double m1_intercept = -0.07913735799581213;
        double m1_distance_decay = 0.24286946330791737;
        double cell_size = 1.0;
        bool cell_size_fallback = false;
        int min_history = 4;
        int candidate_cap = 64;
        bool verifier_enabled = false;
        double navigation_timeout_seconds = 6.0;
        bool force_first_batch_unreachable = false;  // regression-only
        bool require_compute_path_check = false;
        std::string raiom_mode = "M0";
        bool grtom_enabled = false;
        bool snoed_enabled = false;
        bool qams_enabled = false;
        double snoed_tau_seconds = 2.0;
        double snoed_dead_time_seconds = 0.2;
        bool tess_enabled = false;
        bool tess_shadow_only = true;
        // Planner selection and profile-based source reporting are independent.
        // The fast planner comparison keeps the latter disabled for both arms.
        bool tess_takeover_enabled = false;
        bool tess_profile_estimate_enabled = false;
        bool tess_active_stop = false;
        bool tess_use_qam = false;
        bool tess_adaptive_evidence_gate = false;
        bool tess_loo_validation = false;
        bool tess_performance_aligned_aeg = false;
        int tess_max_competitors = 4;
        double tess_log_variance_floor = 1e-4;
        double tess_model_discrepancy_variance = 0.05;
        std::string tess_model_discrepancy_provenance = "FROZEN_GLOBAL_PILOT_V1";
        double tess_max_navigation_seconds = 20.0;
        double tess_min_corrected = 1e-6;
        int tess_min_effective_samples = 3;
        double tess_tau_seconds = 1.2;
        double tess_dead_time_seconds = 0.4;
        double tess_p_valid_min = 0.5;
        int tess_warmup_blocks = 8;
        double tess_candidate_nms_radius_m = 1.0;
        double tess_takeover_absolute_margin = 1e-6;
        double tess_takeover_relative_margin = 0.05;
        double tess_duration_slack_seconds = 0.5;
        double tess_profile_prior_power = 0.0;
        bool tess_linear_drift = false;
        double tess_background_concentration = 0.0;
        double tess_scenario_log_wind_step = 0.10;
        double tess_scenario_log_diffusion_step = 0.10;
        int transport_graph_spacing_cells = 5;
    };

    RuntimeConfig runtime_config_;
    OPGSLV3::PlannerConfig planner_config_;
    OPGSLV3::VerificationConfig verification_config_;
    OPGSLV3::ObservationModelParameters observation_model_;
    bool wind_module_enabled_ = false;
    // RAIOM-GSL transport model
    bool use_transport_model_ = false;
    bool transport_initialized_ = false;
    raiom::TransportGraph transport_graph;
    raiom::PhysicsParams transport_params;
    raiom::SparseNuisanceOrthogonalPlanner snoed_planner_;
    raiom::ActionPredictionCube last_action_cube_;
    std::vector<double> transport_q_cache_;
    SCIM::DualPosterior posterior_;
    SCIM::SpatialInformationPlanner spatial_planner_;
    OPGSLV3::VerificationStatus last_verification_status_;
    OPGSLV3::UpdateDiagnostics last_update_diagnostics_;
    SCIM::PlannerDecision last_planner_decision_;

    bool map_received_ = false;
    bool posterior_initialized_ = false;
    bool source_declared_ = false;
    bool scientific_trace_valid_ = false;
    bool stop_trace_written_ = false;
    std::string end_reason_ = "RUNNING";
    int step_count_ = 0;
    int measurement_count_ = 0;
    int hit_count_ = 0;
    int miss_count_ = 0;
    double elapsed_time_ = 0.0;
    double latest_concentration_ = 0.0;
    double latest_wind_speed_ = 0.0;
    double latest_wind_x_ = 0.0;
    double latest_wind_y_ = 0.0;

    std::mt19937 rng_;
    std::unordered_map<std::int64_t, int> visit_counts_;
    // Control-plane only: freezes VGR's clock while a synchronous planner is
    // scoring actions.  It has no algorithmic payload and is never read by
    // posterior, TESS, or navigation scoring.
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr planner_busy_pub_;
    rclcpp::Client<std_srvs::srv::SetBool>::SharedPtr simulation_pause_client_;
    int planner_pause_depth_ = 0;
    std::vector<OPGSLV3::FeasibleAction> verified_frontiers_;
    std::string run_uuid_;
    std::string source_estimate_trace_file_;
    std::string evidence_trace_file_;
    std::string planner_trace_file_;
    std::string stop_trace_file_;
    std::string parameter_snapshot_file_;
    std::string candidate_trace_file_;
    std::string scim_memory_trace_file_;
    std::string scim_contrast_trace_file_;
    std::string scim_action_trace_file_;
    std::string action_validity_trace_file_;
    std::string declaration_trace_file_;
    std::string source_grid_hash_;
    int candidate_trace_top_k_ = 10;
    std::ofstream source_estimate_stream_;
    std::ofstream evidence_stream_;
    std::ofstream planner_stream_;
    std::ofstream stop_stream_;
    std::ofstream candidate_trace_stream_;
    std::ofstream scim_memory_stream_;
    std::ofstream scim_contrast_stream_;
    std::ofstream scim_action_stream_;
    std::ofstream action_validity_stream_;
    std::ofstream declaration_stream_;
    std::string tess_block_trace_file_;
    std::string tess_source_trace_file_;
    std::string tess_decision_trace_file_;
    std::string tess_pair_detail_trace_file_;
    std::ofstream tess_block_stream_;
    std::ofstream tess_source_stream_;
    std::ofstream tess_decision_stream_;
    std::ofstream tess_pair_detail_stream_;
    std::string tess_reject_trace_file_;
    std::ofstream tess_reject_stream_;
    std::string tess_region_trace_file_;
    std::ofstream tess_region_stream_;
    struct TessEpisode {
        tessv4::LogBlock block;
        double x = 0.0, y = 0.0, z = 0.3, sim_time = 0.0;
        double wind_x = 0.0, wind_y = 0.0;
        bool model_valid = false;
        // [physical scenario][unique transport source node].
        std::vector<std::vector<double>> predicted_log_signature;
    };
    struct TessPhysicsScenario {
        std::string name;
        raiom::PhysicsParams params;
        double wind_x = 0.0;
        double wind_y = 0.0;
    };
    struct TessEstimateSummary {
        bool available = false;
        double x = 0.0, y = 0.0, z = 0.0;
        double entropy = 0.0;
        double credible_radius = 0.0;
        double map_probability = 0.0;
        std::size_t map_source_index = 0;
    };
    std::vector<TessEpisode> tess_episodes_;
    std::vector<std::size_t> tess_all_source_indices_;
    std::vector<int> tess_unique_source_nodes_;
    std::vector<std::size_t> tess_source_to_unique_;
    std::vector<std::vector<tessv3::FopdtState>> tess_fopdt_bank_;
    std::vector<TessPhysicsScenario> tess_cached_physical_scenarios_;
    std::vector<Eigen::MatrixXd> tess_cached_fields_;
    double tess_cached_wind_x_ = std::numeric_limits<double>::quiet_NaN();
    double tess_cached_wind_y_ = std::numeric_limits<double>::quiet_NaN();
    double tess_common_model_discrepancy_variance_ = 0.05;
    bool tess_field_cache_valid_ = false;
    std::vector<tessv4::ScenarioProfile> tess_scenario_profiles_;
    std::vector<double> tess_marginal_profile_weights_;
    TessEstimateSummary tess_estimate_;
    bool tess_model_initialized_ = false;
    int tess_profile_blocks_ = 0;
    int tess_takeover_cycles_ = 0;
    int tess_selected_cycles_ = 0;
    int tess_different_cycles_ = 0;
    int tess_positive_gain_cycles_ = 0;
    int tess_invalid_block_streak_ = 0;
    int tess_pause_cycles_ = 0;
    int tess_v43_committed_action_id_ = -1;
    int tess_v43_commit_accepted_blocks_ = -1;
    // Diagnostic only: elapsed wall time for the active planner call.
    double tess_last_planner_runtime_ms_ = 0.0;

    void initializePosteriorFromMap();
    std::vector<bool> buildSourceValidityMask(const OPGSLV3::GridSpec& spec);
    OPGSLV3::ObservationContext makeObservationContext(double x, double y,
                                                        double z, double concentration) const;
    std::vector<OPGSLV3::FeasibleAction> generateMapFeasibleActions();
    std::vector<OPGSLV3::FeasibleAction> generateRecoveryActions();
    SCIM::PlannerDecision planFeasibleActions(
        const std::vector<OPGSLV3::FeasibleAction>& actions);
    bool applySnoedBundleOrdering(SCIM::PlannerDecision& decision);
    void recordTessMeasurementBlock(double concentration);
    void acquireDeterministicPlannerPause();
    void releaseDeterministicPlannerPause() noexcept;
    bool applyTessOrdering(SCIM::PlannerDecision& decision);
    void ensureTessModelInitialized();
    std::vector<TessPhysicsScenario> makeTessPhysicsScenarios(double wind_x, double wind_y) const;
    bool solveTessScenarioFields(const std::vector<TessPhysicsScenario>& scenarios,
                                 std::vector<Eigen::MatrixXd>& fields,
                                 double* worst_residual = nullptr) const;
    std::vector<tessv3::InputSegment> makeTessExposureSegments(
        const Eigen::MatrixXd& field, int unique_source_column,
        double start_x, double start_y, double goal_x, double goal_y,
        double travel_seconds, double dwell_seconds) const;
    bool updateTessPhysicalModel(TessEpisode& episode);
    bool refreshTessProfiles();
    TessEstimateSummary computeTessEstimate(const std::vector<double>& marginal) const;
    bool buildTessFuturePredictions(
        const SCIM::PlannerDecision& decision,
        const tessv4::RegionPartition& partition,
        std::vector<tessv4::Scenario>& scenarios,
        std::vector<tessv4::ActionMeta>& action_meta,
        std::vector<tessv4::Point2>& region_xy,
        std::vector<double>& history_time_basis,
        std::vector<double>& history_weight,
        double& future_variance) const;
    bool applyPathMetricsToDecision(SCIM::PlannerDecision& decision);
    int visitCount(double x, double y, double z) const;
    void markVisited(double x, double y, double z);
    std::int64_t visitKey(double x, double y, double z) const;
    bool isPointInsideSensorSafeBounds(double x, double y) const;
    double clipToFlightBounds(double z) const;
    void initializeTraceFiles();
    void writeParameterSnapshot() const;
    void writeEvidenceTrace(const OPGSLV3::PosteriorSummary& map_summary,
                            const OPGSLV3::PosteriorSummary& confidence_summary);
    void writeCandidateTrace(const OPGSLV3::ObservationContext& observation,
                             bool detected, const std::vector<double>& preupdate_map,
                             double marginal_predictive_q);
    void writeSourceEstimateTrace(const OPGSLV3::PosteriorSummary& map_summary,
                                  const OPGSLV3::PosteriorSummary& confidence_summary);
    void writePlannerTrace(const SCIM::ActionScore& score, bool selected,
                           int rank, const SCIM::PlannerDecision& decision);
    void writeStopTrace(const OPGSLV3::PosteriorSummary& map_summary,
                        const OPGSLV3::PosteriorSummary& confidence_summary,
                        const std::string& decision, GSLResult result);
    void writeSCIMMemoryTrace();
    void writeSCIMContrastTrace();
    void writeSCIMActionTrace(const SCIM::ActionScore& score, bool selected,
                              const std::string& mode);
    void writeActionValidityTrace(double x, double y, double z, bool accepted,
                                  const std::string& reason);
    void writeDeclarationTrace(const OPGSLV3::PosteriorSummary& map_summary,
                               const OPGSLV3::PosteriorSummary& confidence_summary,
                               const std::string& abstention_reason);
    static std::string stableTraceHash(const std::string& value);
};

// Independent registry identity for A1. The inherited A0 implementation is
// switched to the frozen NCL observation family only by enable_ncl=true.
class OPGSLA1NCL final : public OPGSLSCIMV1 {
public:
    explicit OPGSLA1NCL(std::shared_ptr<rclcpp::Node> node) : OPGSLSCIMV1(std::move(node)) {}
};

}  // namespace GSL

#endif
