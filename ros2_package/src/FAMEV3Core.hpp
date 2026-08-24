#pragma once

// FAME V3 formula-owned pure core. No ROS, evaluator, or source-truth dependency.

#include <cstddef>
#include <string>
#include <vector>

namespace GSL::FAMEV3 {

struct Candidate { int id = 0; double x = 0.0; double y = 0.0; double z = 0.0; };
struct JointState {
    std::vector<double> xi_m0;
    std::vector<double> xi_m1;
    double omega_m0 = 0.5;
    double omega_m1 = 0.5;
};
struct PredictiveField { double q_m0 = 0.5; std::vector<double> q_m1; };
struct UpdateResult { JointState pre; JointState post; PredictiveField predictive; double p_event = 0.5; };
struct RiskResult { double prior = 0.0; double expected_after = 0.0; double delta = 0.0; double binary_delta = 0.0; };

class NonSpatialNullExpert final {
public:
    double predictive() const noexcept;
    void observe(bool event) noexcept;

private:
    double alpha_ = 1.0;
    double beta_ = 1.0;
};

class FrozenSpatialExpert final {
public:
    static constexpr double kIntercept = -0.07913735799581213;
    static constexpr double kDistanceSlope = 0.24286946330791737;
    double predictive(const Candidate&, double pose_x, double pose_y, double pose_z) const noexcept;
};

class JointSourceModelPosterior final {
public:
    void initialize(std::vector<Candidate> candidates);
    UpdateResult update(NonSpatialNullExpert&, const FrozenSpatialExpert&, double pose_x,
                        double pose_y, double pose_z, bool event);
    const JointState& state() const noexcept { return state_; }
    const std::vector<Candidate>& candidates() const noexcept { return candidates_; }
    double predictive(const PredictiveField&) const noexcept;
    RiskResult exactRiskReduction(const PredictiveField&) const;
    static double clamp(double value) noexcept;
    static double bernoulliLogLikelihood(bool event, double q) noexcept;
    static double bernoulliJensenShannon(double q_left, double q_right) noexcept;

private:
    static double sourceRisk(const std::vector<double>& source_mass,
                             const std::vector<Candidate>& candidates);
    std::vector<Candidate> candidates_;
    JointState state_;
    bool initialized_ = false;
};

}  // namespace GSL::FAMEV3
