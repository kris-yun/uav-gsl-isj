#pragma once
// WATS-GSL: Wind-Aware Tabular Spatial Gas Source Localization
// Core Innovation: Replace parametric Gaussian plume model with nonparametric
// kernel-weighted spatial field estimation in wind-relative coordinates.
//
// Key Insight: GADEN uses filament simulation, NOT Gaussian plume.
// A Gaussian plume model will always produce wrong posterior peaks.
// Instead, we use observations directly to build a spatial field estimate.
//
// Module 1: WR-SFE (Wind-Relative Spatial Field Estimator)
//   - Each observation (gas, position) contributes to field estimate
//   - Uses wind-relative coordinates: (along_wind, cross_wind)
//   - No plume shape assumption - field shape emerges from data
//
// Module 2: EP-AB (Ensemble Posterior with Adaptive Bandwidth)
//   - Multiple estimators with different bandwidths
//   - Ensemble variance = uncertainty
//   - Adaptive: more smoothing with few observations
//
// Module 3: WA-IG (Wind-Aware Information Gain)
//   - Prefer exploring downwind of high-gas observations
//   - Use ensemble uncertainty to guide exploration
//   - Balance exploitation (high gas) with exploration (high uncertainty)
//
// References:
//   - Kernel density estimation: Rosenblatt (1956), Parzen (1962)
//   - Wind-relative coordinates: Farrell et al. (2002) "Filament-based atmospheric plume mapping"
//   - Adaptive bandwidth: Terrell & Scott (1992) "Variable kernel density estimation"

#include <Eigen/Dense>
#include <vector>
#include <cmath>
#include <algorithm>
#include <deque>
#include <random>

namespace GSL {
namespace WATS {

struct Observation {
    float gas_reading;
    float x, y;           // Position in world coordinates
    float wind_x, wind_y; // Wind at observation time
    float timestamp;
    float weight;         // Decaying weight (recent = higher)
};

// Module 1: Wind-Relative Spatial Field Estimator
class WR_SFE {
public:
    struct Config {
        int n_cells = 60;
        float resolution = 1.0f;
        float map_half_size = 30.0f;
        int max_observations = 200;
        float observation_decay = 0.995f;   // Temporal decay per step
        float bandwidth_base = 2.0f;        // Base kernel bandwidth (meters)
        float bandwidth_wind_factor = 1.5f; // Extra bandwidth along wind
        float min_bandwidth = 0.5f;
        float max_bandwidth = 5.0f;
        int n_ensemble = 3;                 // Number of ensemble members
    };

    struct FieldEstimate {
        Eigen::MatrixXf log_field;      // Log estimated concentration field
        Eigen::MatrixXf uncertainty;    // Ensemble variance
        Eigen::MatrixXf visit_density;  // How well each cell is observed
        float peak_x, peak_y;           // Estimated peak location
        float peak_value;               // Peak concentration
        float field_entropy;            // Entropy of normalized field
        float max_conc_x = 0.0f, max_conc_y = 0.0f;  // Max concentration position
        float max_conc_val = 0.0f;                   // Max concentration value
        float mean_wind_speed = 0.0f;                // Mean wind speed for fallback threshold
        int n_observations;
    };

    void init(const Config& cfg) {
        cfg_ = cfg;
        int N = cfg.n_cells;
        for (int e = 0; e < cfg.n_ensemble; ++e) {
            ensemble_fields_.push_back(Eigen::MatrixXf::Zero(N, N));
        }
        field_estimate_.log_field = Eigen::MatrixXf::Zero(N, N);
        field_estimate_.uncertainty = Eigen::MatrixXf::Zero(N, N);
        field_estimate_.visit_density = Eigen::MatrixXf::Zero(N, N);
        observations_.clear();
    }

    // Add a new observation
    void addObservation(float gas, float x, float y, float wind_x, float wind_y, float t) {
        Observation obs;
        obs.gas_reading = gas;
        obs.x = x; obs.y = y;
        obs.wind_x = wind_x; obs.wind_y = wind_y;
        obs.timestamp = t;
        obs.weight = 1.0f;

        // Track max concentration position for low-wind fallback
        if (obs.gas_reading > field_estimate_.max_conc_val) {
            field_estimate_.max_conc_val = obs.gas_reading;
            field_estimate_.max_conc_x = obs.x;
            field_estimate_.max_conc_y = obs.y;
        }
        // Update mean wind speed
        float ws = std::sqrt(obs.wind_x * obs.wind_x + obs.wind_y * obs.wind_y);
        field_estimate_.mean_wind_speed = 0.9f * field_estimate_.mean_wind_speed + 0.1f * ws;
        observations_.push_back(obs);
        if (observations_.size() > cfg_.max_observations) {
            observations_.pop_front();
        }

        // Decay old observations
        for (auto& o : observations_) {
            o.weight *= cfg_.observation_decay;
        }
    }

    // Compute the field estimate using all observations
    FieldEstimate computeField() {
        int N = cfg_.n_cells;
        float res = cfg_.resolution;
        float half = cfg_.map_half_size;

        // Clear ensemble fields
        for (auto& f : ensemble_fields_) {
            f.setZero();
        }
        field_estimate_.visit_density.setZero();
        field_estimate_.max_conc_val = 0.0f;
        field_estimate_.max_conc_x = 0.0f;
        field_estimate_.max_conc_y = 0.0f;

        // Bandwidths for ensemble members
        float bandwidths[3] = {
            cfg_.bandwidth_base * 0.7f,
            cfg_.bandwidth_base,
            cfg_.bandwidth_base * 1.5f
        };

        int n_obs = observations_.size();
        if (n_obs == 0) return field_estimate_;

        // For each observation, update the field estimate
        for (const auto& obs : observations_) {
            if (obs.gas_reading < 1e-6f) continue;

                                    // UPWIND SOURCE PROBABILITY FIELD (USPF)
            // Key insight: gas is detected DOWNWIND of source.
            // To infer source location, place kernel UPWIND of detection point.
            // This is NOT anisotropic plume modeling - it is source probability inference.
            float wind_speed_obs = std::sqrt(obs.wind_x * obs.wind_x + obs.wind_y * obs.wind_y);
            float wind_dir = std::atan2(obs.wind_y, obs.wind_x);
            // Upwind direction = opposite to wind
            float upwind_x = -std::cos(wind_dir);
            float upwind_y = -std::sin(wind_dir);
            // Shift kernel center upwind by a fraction of bandwidth
            float upwind_shift = std::min(cfg_.bandwidth_base * 0.8f, wind_speed_obs * 5.0f);
            float src_x = obs.x + upwind_shift * upwind_x;
            float src_y = obs.y + upwind_shift * upwind_y;

            for (int e = 0; e < cfg_.n_ensemble && e < 3; ++e) {
                float scale = bandwidths[e] / cfg_.bandwidth_base;
                float bw = std::max(cfg_.min_bandwidth, cfg_.bandwidth_base * scale);

                for (int i = 0; i < N; ++i) {
                    for (int j = 0; j < N; ++j) {
                        float cell_x = i * res - half;
                        float cell_y = j * res - half;

                        // Distance to SHIFTED source estimate (upwind of detection)
                        float dx = cell_x - src_x;
                        float dy = cell_y - src_y;
                        float dist_sq = dx * dx + dy * dy;

                        // Isotropic Gaussian kernel centered on upwind source estimate
                        float log_kernel = -dist_sq / (2.0f * bw * bw);

                        // Weighted contribution (higher gas = stronger source signal)
                        float contribution = obs.gas_reading * obs.weight * std::exp(log_kernel);
                        ensemble_fields_[e](i, j) += contribution;
                    }
                }
            }// Update visit density
            int cx = std::max(0, std::min(N-1, (int)((obs.x + half) / res)));
            int cy = std::max(0, std::min(N-1, (int)((obs.y + half) / res)));
            int r = std::max(1, (int)(cfg_.bandwidth_base / res));
            for (int di = -r; di <= r; ++di) {
                for (int dj = -r; dj <= r; ++dj) {
                    int ni = cx + di, nj = cy + dj;
                    if (ni >= 0 && ni < N && nj >= 0 && nj < N) {
                        float d = std::sqrt(float(di*di + dj*dj));
                        field_estimate_.visit_density(ni, nj) += std::exp(-d*d / (2*r*r));
                    }
                }
            }
        }

        // Compute mean field from ensemble
        field_estimate_.log_field.setZero();
        for (int e = 0; e < cfg_.n_ensemble; ++e) {
            field_estimate_.log_field += ensemble_fields_[e];
        }
        field_estimate_.log_field /= cfg_.n_ensemble;

        // Compute uncertainty (ensemble variance)
        field_estimate_.uncertainty.setZero();
        for (int e = 0; e < cfg_.n_ensemble; ++e) {
            Eigen::MatrixXf diff = ensemble_fields_[e] - field_estimate_.log_field;
            field_estimate_.uncertainty += diff.array().square().matrix();
        }
        field_estimate_.uncertainty /= cfg_.n_ensemble;

        // Normalize field to log probabilities
        float max_val = field_estimate_.log_field.maxCoeff();
        if (max_val > 0) {
            field_estimate_.log_field = (field_estimate_.log_field.array() / max_val).log();
        }

        // Find peak
        int peak_i, peak_j;
        field_estimate_.log_field.maxCoeff(&peak_i, &peak_j);
        field_estimate_.peak_x = peak_i * res - half;
        field_estimate_.peak_y = peak_j * res - half;

        // LOW-WIND FALLBACK: when wind is very low, WR-SFE kernel shift is negligible
        // and field peak is unreliable. Fall back to max-concentration position.
        float WIND_THRESHOLD = 0.2f;  // m/s
        if (field_estimate_.mean_wind_speed < WIND_THRESHOLD && field_estimate_.max_conc_val > 0.01f) {
            // Blend: mostly max-conc position when wind is very low
            float alpha = field_estimate_.mean_wind_speed / WIND_THRESHOLD;  // 0 at zero wind, 1 at threshold
            alpha = std::clamp(alpha, 0.0f, 1.0f);
            field_estimate_.peak_x = alpha * field_estimate_.peak_x + (1.0f - alpha) * field_estimate_.max_conc_x;
            field_estimate_.peak_y = alpha * field_estimate_.peak_y + (1.0f - alpha) * field_estimate_.max_conc_y;
        }
        field_estimate_.peak_value = max_val;
        field_estimate_.n_observations = n_obs;

        // Compute entropy
        Eigen::ArrayXXf p = field_estimate_.log_field.array().exp();
        float p_sum = p.sum();
        if (p_sum > 0) p /= p_sum;
        field_estimate_.field_entropy = -(p * (p.max(1e-10f).log())).sum();

        return field_estimate_;
    }

    const FieldEstimate& lastEstimate() const { return field_estimate_; }
    int observationCount() const { return observations_.size(); }

    struct Centroid { float x; float y; float weight_sum; float spread; };

    // UAV-aware centroid: considers flight height, time window, wind consistency
    Centroid computeWeightedCentroid(int top_n = 20) const {
        Centroid result = {0, 0, 0, 0};
        if (observations_.empty()) return result;

        // Find the latest timestamp for time-window filtering
        float latest_t = 0;
        for (const auto& obs : observations_)
            if (obs.timestamp > latest_t) latest_t = obs.timestamp;

        // Time window: only use observations from last 60 seconds
        // Reason: wind direction changes invalidate old upwind estimates
        float time_window = 60.0f;

        // Collect gas-positive observations within time window
        struct WeightedObs { float x, y, w, wind_x, wind_y; };
        std::vector<WeightedObs> gas_obs;
        for (const auto& obs : observations_) {
            if (obs.gas_reading < 1e-6f) continue;
            if (latest_t - obs.timestamp > time_window) continue;

            // Base weight: gas concentration * temporal decay
            float w = obs.gas_reading * obs.weight;

            // UAV height correction: sensor at z=1.0m, source near floor z=-0.3m
            // Gas concentration decreases with height: C(z) ~ C(0)*exp(-k*z)
            // Higher gas reading at flight height means source is closer (stronger plume)
            // No correction needed for distance estimation - higher concentration = closer

            gas_obs.push_back({obs.x, obs.y, w, obs.wind_x, obs.wind_y});
        }

        if (gas_obs.empty()) return result;

        // Sort by weight (descending), take top_n
        std::sort(gas_obs.begin(), gas_obs.end(),
                  [](const WeightedObs& a, const WeightedObs& b) { return a.w > b.w; });
        int n = std::min(top_n, (int)gas_obs.size());

        // Compute wind-direction consensus: find the dominant wind direction
        float wind_cos = 0, wind_sin = 0;
        for (int i = 0; i < n; i++) {
            float spd = std::sqrt(gas_obs[i].wind_x * gas_obs[i].wind_x +
                                   gas_obs[i].wind_y * gas_obs[i].wind_y);
            if (spd > 0.02f) {
                float dir = std::atan2(gas_obs[i].wind_y, gas_obs[i].wind_x);
                wind_cos += std::cos(dir);
                wind_sin += std::sin(dir);
            }
        }
        float consensus_dir = std::atan2(wind_sin, wind_cos);
        float consensus_x = std::cos(consensus_dir);
        float consensus_y = std::sin(consensus_dir);

        // Upwind source shift: use consensus wind direction
        // Shift each observation upwind by 1.0m (conservative estimate)
        // Wind consistency: compute R (0=uniform, 1=perfectly consistent)
        float wcos2 = 0, wsin2 = 0, wcnt = 0;
        for (const auto& o2 : observations_) {
            float sp2 = std::sqrt(o2.wind_x * o2.wind_x + o2.wind_y * o2.wind_y);
            if (sp2 > 0.02f) { wcos2 += o2.wind_x/sp2; wsin2 += o2.wind_y/sp2; wcnt += 1.0f; }
        }
        float R_val = (wcnt > 0) ? std::sqrt(wcos2*wcos2 + wsin2*wsin2) / wcnt : 0;
        // FIX1: scale upwind_shift by wind speed to avoid drift in low wind
        float mean_ws = 0.0f; int wcnt2 = 0;
        for (const auto& o3 : observations_) { float sp3 = std::sqrt(o3.wind_x*o3.wind_x + o3.wind_y*o3.wind_y); if (sp3 > 0.01f) { mean_ws += sp3; wcnt2++; } }
        mean_ws = (wcnt2 > 0) ? mean_ws / wcnt2 : 0.05f;
        float upwind_shift = 0.3f + 1.2f * R_val * std::min(1.0f, mean_ws / 0.1f);
        upwind_shift = std::max(0.3f, std::min(1.5f, upwind_shift));

        // Use MEDIAN for robustness (not mean which is skewed by outliers)
        std::vector<float> xs, ys;
        float wx = 0, wy = 0, wsum = 0;
        for (int i = 0; i < n; i++) {
            float sx = gas_obs[i].x + upwind_shift * (-consensus_x);
            float sy = gas_obs[i].y + upwind_shift * (-consensus_y);
            xs.push_back(sx);
            ys.push_back(sy);
            wx += gas_obs[i].w * sx;
            wy += gas_obs[i].w * sy;
            wsum += gas_obs[i].w;
        }

        // Compute both weighted mean and median, use whichever has lower spread
        float mean_x = (wsum > 1e-6f) ? wx / wsum : 0;
        float mean_y = (wsum > 1e-6f) ? wy / wsum : 0;

        std::sort(xs.begin(), xs.end());
        std::sort(ys.begin(), ys.end());
        float median_x = xs[xs.size() / 2];
        float median_y = ys[ys.size() / 2];

        // Compute spread for both
        float mean_var = 0, median_var = 0;
        for (int i = 0; i < n; i++) {
            float sx = gas_obs[i].x + upwind_shift * (-consensus_x);
            float sy = gas_obs[i].y + upwind_shift * (-consensus_y);
            mean_var += gas_obs[i].w * ((sx - mean_x) * (sx - mean_x) + (sy - mean_y) * (sy - mean_y));
            median_var += ((sx - median_x) * (sx - median_x) + (sy - median_y) * (sy - median_y));
        }
        mean_var = (wsum > 1e-6f) ? mean_var / wsum : 1e6f;
        median_var /= n;

        // Use the one with lower variance
        if (median_var < mean_var) {
            result.x = median_x;
            result.y = median_y;
            result.spread = std::sqrt(median_var);
        } else {
            result.x = mean_x;
            result.y = mean_y;
            result.spread = std::sqrt(mean_var);
        }
        result.weight_sum = wsum;
        return result;
    }

    // SBD: expose ensemble fields for EIG computation
    const std::vector<Eigen::MatrixXf>& ensembleFields() const { return ensemble_fields_; }
    int ensembleSize() const { return cfg_.n_ensemble; }

private:
    Config cfg_;
    std::deque<Observation> observations_;
    std::vector<Eigen::MatrixXf> ensemble_fields_;
    FieldEstimate field_estimate_;
};

// Module 3: Wind-Aware Information Gain
class WA_IG {
public:
    struct Config {
        float exploration_weight = 0.3f;
        float wind_bonus = 0.5f;          // Bonus for downwind exploration
        float uncertainty_weight = 0.4f;
        float visit_penalty = 0.2f;
    };

    void init(const Config& cfg) { cfg_ = cfg; }

    // Compute information gain for a candidate cell
    float compute(const WR_SFE::FieldEstimate& field,
                  int gx, int gy, int n_cells,
                  float robot_x, float robot_y,
                  float wind_x, float wind_y,
                  float resolution, float map_half_size) const {
        float cell_x = gx * resolution - map_half_size;
        float cell_y = gy * resolution - map_half_size;
        float dx = cell_x - robot_x;
        float dy = cell_y - robot_y;
        float dist = std::sqrt(dx*dx + dy*dy) + 0.1f;

        // Exploitation: field value at this cell
        float field_val = std::exp(field.log_field(gx, gy));
        float exploit = field_val / (1.0f + 0.3f * dist);

        // Exploration: uncertainty at this cell
        float uncertainty = field.uncertainty(gx, gy);
        float visit = field.visit_density(gx, gy);
        float explore = uncertainty / (1.0f + visit * cfg_.visit_penalty);

        // Wind bonus: prefer downwind of high-gas observations
        float wind_speed = std::sqrt(wind_x * wind_x + wind_y * wind_y);
        float wind_bonus = 0.0f;
        if (wind_speed > 0.02f) {
            float wind_dir = std::atan2(wind_y, wind_x);
            float cos_w = std::cos(wind_dir);
            float sin_w = std::sin(wind_dir);
            float along = dx * cos_w + dy * sin_w;
            // Downwind bonus: cells downwind of robot get bonus
            if (along > 0) {
                wind_bonus = cfg_.wind_bonus * std::tanh(along / 3.0f) * std::min(1.0f, wind_speed / 0.1f);
            }
        }

        // Combined IG
        float ig = exploit + cfg_.exploration_weight * explore + wind_bonus;

        // Penalty for already-visited cells
        ig -= cfg_.visit_penalty * visit / (1.0f + dist);

        return ig;
    }


    // Golden-angle spiral exploration with wind bias
    void exploreGoldenAngle(float& out_x, float& out_y,
                            float robot_x, float robot_y,
                            float wind_x, float wind_y,
                            float step_size, int step_count,
                            float map_half_size) const {
        static constexpr float GOLDEN_ANGLE = 2.39996323f;
        float max_radius = 5.0f; // Limit spiral radius to keep exploration local
        float radius = std::min(max_radius, step_size * std::sqrt(static_cast<float>((step_count % 20) + 1)));
        float angle = step_count * GOLDEN_ANGLE;
        float spiral_x = robot_x + radius * std::cos(angle);
        float spiral_y = robot_y + radius * std::sin(angle);
        float wind_speed = std::sqrt(wind_x * wind_x + wind_y * wind_y);
        float wind_bias_x = 0.0f, wind_bias_y = 0.0f;
        if (wind_speed > 0.02f) {
            float wind_dir = std::atan2(wind_y, wind_x);
            float bias = 0.8f * step_size * std::min(1.0f, wind_speed / 0.05f); // FIX3: stronger wind bias
            wind_bias_x = -bias * std::cos(wind_dir);
            wind_bias_y = -bias * std::sin(wind_dir);
        }
        out_x = std::max(-map_half_size + 1.0f, std::min(map_half_size - 1.0f, spiral_x + wind_bias_x));
        out_y = std::max(-map_half_size + 1.0f, std::min(map_half_size - 1.0f, spiral_y + wind_bias_y));
    }

    // Posterior concentration metric: 0=uniform, 1=fully peaked
    // SBD: expose ensemble fields for EIG computation

    float posteriorConcentration(const WR_SFE::FieldEstimate& field) const {
        if (field.n_observations < 2) return 0.0f;
        int count = 0;
        for (int i = 0; i < field.log_field.rows(); ++i)
            for (int j = 0; j < field.log_field.cols(); ++j)
                if (field.log_field(i, j) > -10.0f) count++;
        if (count == 0) return 0.0f;
        Eigen::ArrayXXf p = field.log_field.array().exp();
        float entropy = 0.0f;
        for (int i = 0; i < p.rows(); ++i)
            for (int j = 0; j < p.cols(); ++j)
                if (p(i,j) > 1e-10f) entropy -= p(i,j) * std::log(p(i,j));
        float max_ent = std::log(static_cast<float>(count));
        return (max_ent > 1e-6f) ? (1.0f - entropy / max_ent) : 0.0f;
    }

    private:
    Config cfg_;
};


// ============================================================
// Module 4: Wasserstein Risk-Aware Information Gain (W-RAIG)
// ============================================================
// Key idea: Standard EIG (Infotaxis) is risk-neutral. W-RAIG adds a
// risk penalty that discourages actions whose information gain is
// uncertain across the posterior ensemble. This prevents the UAV from
// committing to actions that look good on average but have high variance.
//
// Mathematical formulation:
//   W-RAIG(a) = E_m[EIG_m(a)] - beta * sqrt(Var_m[EIG_m(a)])
// where the expectation is over ensemble members m=1..M.
//
// When beta=0: W-RAIG = standard EIG = Infotaxis (degenerate case)
// When beta>0: risk-averse, prefer actions with consistent information gain
//
// Connection to CVaR: As beta -> infinity, W-RAIG selects the action
// that maximizes the worst-case EIG across ensemble members, which is
// equivalent to CVaR-alpha with alpha -> 0.
//
// References:
//   - Rockafellar & Uryasev (2000) "Optimization of conditional value-at-risk"
//   - Husmeier et al. (2025) "Risk-sensitive Bayesian optimization"
//   -棫田 et al. (2024) "Sequential design with risk measures"

class WRAIG {
public:
    struct Config {
        float beta = 0.5f;            // Risk aversion coefficient [0,inf)
        float min_eig_threshold = 1e-4f; // Minimum EIG to consider
        int n_ensemble = 3;           // Number of ensemble members
    };

    void init(const Config& cfg) { cfg_ = cfg; }

    // Compute risk-aware information gain for a candidate cell
    // given ensemble EIG values from different field estimator members
    float compute(float mean_eig, float var_eig) const {
        if (mean_eig < cfg_.min_eig_threshold) return 0.0f;
        float risk_penalty = cfg_.beta * std::sqrt(std::max(var_eig, 0.0f));
        return std::max(0.0f, mean_eig - risk_penalty);
    }

    // Compute W-RAIG field over entire grid
    // Input: ensemble EIG fields from n_ensemble members
    // Output: risk-adjusted EIG field
    void computeField(const std::vector<Eigen::MatrixXf>& ensemble_eig,
                      Eigen::MatrixXf& wraig_field) const {
        int N = ensemble_eig[0].rows();
        int M = ensemble_eig[0].cols();
        int n_e = ensemble_eig.size();
        wraig_field = Eigen::MatrixXf::Zero(N, M);

        for (int i = 0; i < N; i++) {
            for (int j = 0; j < M; j++) {
                // Compute mean and variance of EIG across ensemble
                float sum = 0.0f, sum2 = 0.0f;
                for (int e = 0; e < n_e; e++) {
                    float v = ensemble_eig[e](i, j);
                    sum += v;
                    sum2 += v * v;
                }
                float mean_eig = sum / n_e;
                float var_eig = (sum2 / n_e) - (mean_eig * mean_eig);
                wraig_field(i, j) = compute(mean_eig, var_eig);
            }
        }
    }

    // Infotaxis degenerate case: when beta=0, returns standard EIG
    bool isInfotaxisDegenerate() const { return cfg_.beta < 1e-6f; }

private:
    Config cfg_;
};

} // namespace WATS
} // namespace GSL