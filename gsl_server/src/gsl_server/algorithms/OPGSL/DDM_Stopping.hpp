#pragma once
// DDM_Stopping: Drift-Diffusion Model for GSL Search Termination
// Based on Gold & Shadlen (2007) "The neural basis of decision making"
// with Urgency-Gating from Cisek et al. (2009) "Racing in the brain"
//
// Key insight: GSL search = perceptual decision making under uncertainty.
// The UAV accumulates evidence (log-likelihood ratio) about source location
// until reaching a confidence threshold, with urgency gating for time pressure.

#include <cmath>
#include <deque>
#include <algorithm>

namespace GSL {
namespace DDM {

struct DDMConfig {
    float alpha = 0.05f;           // Type I error rate (false positive)
    float beta = 0.05f;            // Type II error rate (false negative)
    float gamma_urgency = 0.005f;  // Urgency decay rate (higher = more urgent)
    float theta_min = 0.5f;        // Minimum threshold (never stop below this)
    float leak_lambda = 0.01f;     // Evidence leak rate (prevents stale evidence)
    float noise_sigma = 0.1f;      // Observation noise std
    int min_obs = 10;              // Minimum observations before stopping allowed
    float min_time = 20.0f;        // Minimum time before stopping allowed
};

class DDMStopping {
public:
    explicit DDMStopping(const DDMConfig& cfg = DDMConfig{}) : cfg_(cfg) {
        // Compute optimal fixed threshold from SPRT
        float alpha = std::max(cfg.alpha, 1e-6f);
        float beta_val = std::max(cfg.beta, 1e-6f);
        theta_fixed_ = std::log((1.0f - beta_val) / alpha);
        evidence_ = 0.0f;
        n_obs_ = 0;
        elapsed_ = 0.0f;
        stopped_ = false;
        stop_reason_ = "";
    }

    // Add a new observation: log-likelihood ratio for source at MAP vs null
    // positive = evidence FOR source at current MAP
    // negative = evidence AGAINST
    void addObservation(float log_likelihood_ratio, float current_time) {
        n_obs_++;
        elapsed_ = current_time;

        // DDM accumulation with leak (Ornstein-Uhlenbeck process)
        // dx = (mu - lambda*x) dt + sigma*dW
        // Discretized: x_{t+1} = x_t + llr - lambda*x_t + noise
        float noise = cfg_.noise_sigma * 0.01f;  // Small noise for deterministic-ish behavior
        evidence_ = evidence_ + log_likelihood_ratio - cfg_.leak_lambda * evidence_ + noise;

        // Clamp to prevent overflow
        evidence_ = std::clamp(evidence_, -100.0f, 100.0f);
    }

    // Check if search should stop
    // Returns true if evidence has crossed the adaptive threshold
    bool shouldStop() const {
        if (n_obs_ < cfg_.min_obs) return false;
        if (elapsed_ < cfg_.min_time) return false;

        float theta = getAdaptiveThreshold();
        return std::abs(evidence_) >= theta;
    }

    // Get the current adaptive threshold with urgency gating
    // theta(t) = theta_0 * exp(-gamma*t) + theta_min
    float getAdaptiveThreshold() const {
        float urgency_factor = std::exp(-cfg_.gamma_urgency * elapsed_);
        return theta_fixed_ * urgency_factor + cfg_.theta_min;
    }

    // Get current evidence level (for diagnostics)
    float getEvidence() const { return evidence_; }
    float getEvidenceRatio() const {
        float theta = getAdaptiveThreshold();
        return theta > 0.0f ? std::abs(evidence_) / theta : 0.0f;
    }
    int getObsCount() const { return n_obs_; }
    bool hasStopped() const { return stopped_; }

    // Reset for new episode
    void reset() {
        evidence_ = 0.0f;
        n_obs_ = 0;
        elapsed_ = 0.0f;
        stopped_ = false;
        stop_reason_ = "";
    }

    DDMConfig cfg_;
private:
    float theta_fixed_;   // SPRT-optimal fixed threshold
    float evidence_;      // Accumulated evidence (log-likelihood ratio)
    int n_obs_;           // Number of observations
    float elapsed_;       // Elapsed time
    bool stopped_;
    std::string stop_reason_;
};

// Helper: compute log-likelihood ratio for source hypothesis
// Given: current gas reading z, MAP position (mx,my), robot position (rx,ry)
// Uses simple Gaussian plume model for likelihood
inline float computeLogLikelihoodRatio(
    float z_reading,      // Current gas concentration
    float mx, float my,   // MAP source estimate
    float rx, float ry,   // Robot position
    float sigma_source = 1.0f,  // Source model noise
    float sigma_null = 2.0f     // Null model noise (uniform background)
) {
    // Distance from robot to MAP estimate
    float dx = rx - mx, dy = ry - my;
    float dist2 = dx*dx + dy*dy;

    // Source hypothesis: concentration decreases with distance from source
    // P(z | source at (mx,my)) = N(z; A*exp(-dist2/(2*sigma_s^2)), noise^2)
    float mu_source = std::exp(-dist2 / (2.0f * sigma_source * sigma_source));
    float log_p_source = -0.5f * (z_reading - mu_source) * (z_reading - mu_source);

    // Null hypothesis: uniform background noise
    // P(z | no source) = N(z; 0, sigma_null^2)
    float log_p_null = -0.5f * (z_reading * z_reading) / (sigma_null * sigma_null);

    return log_p_source - log_p_null;
}

}  // namespace DDM
}  // namespace GSL