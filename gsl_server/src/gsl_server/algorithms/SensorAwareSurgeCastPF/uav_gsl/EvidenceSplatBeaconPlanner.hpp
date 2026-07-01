#pragma once
#include <algorithm>
#include <cmath>
#include <limits>
#include <string>
#include <vector>

namespace uav_gsl {

struct EvidenceSample {
  double x{0.0};
  double y{0.0};
  double gas_ppm{0.0};
  bool hit{false};
  double wind_dir_flow_to_rad{0.0};
  double wind_speed_ms{0.0};
  double sensor_confidence{1.0};
  double age_s{0.0};
};

struct EvidenceSplatParams {
  double alpha0{0.6};
  double beta0{0.6};
  double sigma_crosswind_m{1.4};
  double sigma_downwind_m{0.8};
  double recency_tau_s{60.0};
  double coverage_saturation{3.0};
  int min_hits{2};
  int min_nohits{6};
  double min_boundary_support{0.18};
  int min_angular_bins{3};
  std::vector<double> local_radii{1.0, 1.5, 2.0};
  std::vector<double> medium_radii{2.0, 3.0, 4.0};
  std::vector<double> global_radii{3.0, 4.5, 6.0};
  int n_angles{16};
  double w_boundary{3.0};
  double w_frontier{1.4};
  double w_visibility{0.6};
  double w_kappa{0.5};
  double w_sparse{0.8};
  double w_saturated{0.8};
  double w_path{0.25};
  double w_revisit{0.55};
};

struct Candidate {
  double x{0.0};
  double y{0.0};
  std::string family{"coverage_frontier"};
  double radius_m{0.0};
};

struct CandidateScore {
  Candidate candidate;
  double score{-std::numeric_limits<double>::infinity()};
  double hit_support{0.0};
  double nohit_support{0.0};
  double coverage_score{0.0};
  double p_hit{0.5};
  double boundary_score{0.0};
  double confidence_weight{0.0};
  double frontier_gain{0.0};
  double boundary_kappa{0.0};
  int angular_bins_covered{0};
  bool support_ready{false};
};

class EvidenceSplatBeaconPlanner {
 public:
  explicit EvidenceSplatBeaconPlanner(EvidenceSplatParams params = {}) : params_(std::move(params)) {}

  void clear() { samples_.clear(); }
  void addSample(const EvidenceSample& s) { samples_.push_back(s); }
  const std::vector<EvidenceSample>& samples() const { return samples_; }

  CandidateScore select(double pose_x, double pose_y) const {
    const auto cands = generateCandidates(pose_x, pose_y);
    CandidateScore best;
    for (const auto& c : cands) {
      auto sc = scoreCandidate(c, pose_x, pose_y);
      if (sc.score > best.score) best = sc;
    }
    return best;
  }

  std::string regime() const {
    if (samples_.size() < 12) return "early_bootstrap";
    int recent = std::min<int>(30, samples_.size());
    int hits = 0;
    for (int i = static_cast<int>(samples_.size()) - recent; i < static_cast<int>(samples_.size()); ++i) {
      if (samples_[i].hit) ++hits;
    }
    const double hit_rate = static_cast<double>(hits) / std::max(1, recent);
    const int recent_nohits = recent - hits;
    const double boundary = estimateBoundarySupport();
    if (hit_rate > 0.85 && recent_nohits < params_.min_nohits) return "saturated_unsupported";
    if (hit_rate < 0.15 || boundary < params_.min_boundary_support) return "sparse_or_unsupported";
    return "nominal_or_supported";
  }

 private:
  EvidenceSplatParams params_;
  std::vector<EvidenceSample> samples_;

  static double clamp(double v, double lo, double hi) { return std::max(lo, std::min(hi, v)); }

  double kernel(const EvidenceSample& s, double x, double y) const {
    const double dx = x - s.x;
    const double dy = y - s.y;
    const double theta = s.wind_dir_flow_to_rad;
    const double d_down = dx * std::cos(theta) + dy * std::sin(theta);
    const double d_cross = -dx * std::sin(theta) + dy * std::cos(theta);
    const double k = std::exp(-0.5 * (std::pow(d_cross / params_.sigma_crosswind_m, 2.0) +
                                      std::pow(d_down / params_.sigma_downwind_m, 2.0)));
    const double recency = std::exp(-std::max(0.0, s.age_s) / std::max(1e-6, params_.recency_tau_s));
    const double wind_conf = clamp(s.wind_speed_ms / 0.6, 0.2, 1.0);
    return k * clamp(s.sensor_confidence, 0.0, 1.0) * recency * wind_conf;
  }

  void supportAt(double x, double y, double& hit, double& nohit, double& coverage, double& p_hit,
                 double& weighted_boundary) const {
    hit = 0.0;
    nohit = 0.0;
    for (const auto& s : samples_) {
      const double k = kernel(s, x, y);
      if (s.hit) hit += k; else nohit += k;
    }
    coverage = hit + nohit;
    p_hit = (params_.alpha0 + hit) / (params_.alpha0 + params_.beta0 + coverage);
    const double boundary = 4.0 * p_hit * (1.0 - p_hit);
    const double conf = std::min(1.0, coverage / std::max(1e-6, params_.coverage_saturation));
    weighted_boundary = boundary * conf;
  }

  double estimateBoundarySupport() const {
    if (samples_.empty()) return 0.0;
    const int n = std::min<int>(50, samples_.size());
    double sum = 0.0;
    for (int i = static_cast<int>(samples_.size()) - n; i < static_cast<int>(samples_.size()); ++i) {
      double h, nh, cov, p, b;
      supportAt(samples_[i].x, samples_[i].y, h, nh, cov, p, b);
      sum += b;
    }
    return sum / std::max(1, n);
  }

  int angularBinsCovered(double cx, double cy) const {
    std::vector<int> seen(params_.n_angles, 0);
    constexpr double PI = 3.14159265358979323846;
    for (const auto& s : samples_) {
      double ang = std::atan2(s.y - cy, s.x - cx);
      int idx = static_cast<int>(((ang + PI) / (2.0 * PI)) * params_.n_angles);
      idx = std::max(0, std::min(params_.n_angles - 1, idx));
      seen[idx] = 1;
    }
    int count = 0;
    for (int v : seen) count += v;
    return count;
  }

  bool supportReady(double cx, double cy) const {
    int hits = 0;
    for (const auto& s : samples_) if (s.hit) ++hits;
    int nohits = static_cast<int>(samples_.size()) - hits;
    return hits >= params_.min_hits && nohits >= params_.min_nohits &&
           estimateBoundarySupport() >= params_.min_boundary_support &&
           angularBinsCovered(cx, cy) >= params_.min_angular_bins;
  }

  std::vector<Candidate> generateCandidates(double pose_x, double pose_y) const {
    std::vector<double> radii = params_.local_radii;
    const auto r = regime();
    if (r == "sparse_or_unsupported" || r == "saturated_unsupported") {
      radii.insert(radii.end(), params_.medium_radii.begin(), params_.medium_radii.end());
      radii.insert(radii.end(), params_.global_radii.begin(), params_.global_radii.end());
    }
    std::vector<Candidate> out;
    constexpr double PI = 3.14159265358979323846;
    for (double rad : radii) {
      for (int i = 0; i < params_.n_angles; ++i) {
        const double a = 2.0 * PI * static_cast<double>(i) / static_cast<double>(params_.n_angles);
        Candidate c;
        c.x = pose_x + rad * std::cos(a);
        c.y = pose_y + rad * std::sin(a);
        c.radius_m = rad;
        c.family = (rad <= params_.local_radii.back()) ? "boundary_refinement" : "coverage_frontier";
        if (r == "saturated_unsupported" && rad >= params_.medium_radii.front()) c.family = "saturated_escape";
        out.push_back(c);
      }
    }
    return out;
  }

  CandidateScore scoreCandidate(const Candidate& c, double pose_x, double pose_y) const {
    CandidateScore sc;
    sc.candidate = c;
    supportAt(c.x, c.y, sc.hit_support, sc.nohit_support, sc.coverage_score, sc.p_hit, sc.boundary_score);
    sc.confidence_weight = std::min(1.0, sc.coverage_score / std::max(1e-6, params_.coverage_saturation));
    sc.frontier_gain = std::max(0.0, 1.0 - sc.confidence_weight);
    sc.boundary_kappa = std::min(sc.hit_support, sc.nohit_support) /
                        std::max(1e-6, sc.hit_support + sc.nohit_support + params_.alpha0 + params_.beta0);
    sc.angular_bins_covered = angularBinsCovered(c.x, c.y);
    sc.support_ready = supportReady(c.x, c.y);
    const double dist = std::hypot(c.x - pose_x, c.y - pose_y);
    const double revisit = std::max(0.0, sc.confidence_weight - 0.85);
    const auto r = regime();
    const double sparse_bonus = (r == "sparse_or_unsupported" && c.family == "coverage_frontier") ? 1.0 : 0.0;
    const double saturated_bonus = (r == "saturated_unsupported" && c.family == "saturated_escape" && sc.p_hit < 0.65) ? 1.0 : 0.0;
    const double visibility_gain = std::min(1.0, static_cast<double>(sc.angular_bins_covered) / std::max(1, params_.min_angular_bins));
    sc.score = params_.w_boundary * sc.boundary_score +
               params_.w_frontier * sc.frontier_gain +
               params_.w_visibility * visibility_gain +
               params_.w_kappa * sc.boundary_kappa +
               params_.w_sparse * sparse_bonus +
               params_.w_saturated * saturated_bonus -
               params_.w_path * dist -
               params_.w_revisit * revisit;
    return sc;
  }
};

}  // namespace uav_gsl
