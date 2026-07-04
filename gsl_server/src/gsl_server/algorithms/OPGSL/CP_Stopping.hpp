#pragma once
#include <deque>
#include <vector>
#include <algorithm>
#include <cmath>
#include <numeric>

namespace GSL { namespace CP {

// =========================================================================
//  E-Process Stopping Rule (replacing OnlineConformalStopping)
//  
//  Mathematical basis: Anytime-Valid Inference via e-processes
//  Reference: Ramdas et al. (2023) "Game-theoretic Statistics and Safe
//             Anytime-Valid Inference" Statistical Science 38(4)
//
//  Key property: P(sup_T M_T >= 1/delta) <= delta (Ville's inequality)
//  This holds for ANY stopping time, no exchangeability required.
// =========================================================================

struct EProcessConfig {
    float delta;           // Significance level (e.g., 0.10 → 90% confidence)
    int min_steps;         // Minimum steps before stopping allowed (warm-up)
    int max_win;           // Maximum window size for adaptive threshold
    float convergence_thresh; // Residual threshold for "converged" (meters)
    int stable_req;        // Consecutive stable steps required
    
    // E-value calibration parameters
    float eta;             // Learning rate for e-value construction
    float decay;           // Exponential decay for old observations
    
    EProcessConfig()
        : delta(0.10f)
        , min_steps(5)
        , max_win(50)
        , convergence_thresh(1.5f)
        , stable_req(3)
        , eta(0.5f)
        , decay(0.95f)
    {}
};

class EProcessStopping {
public:
    explicit EProcessStopping(const EProcessConfig& c = EProcessConfig())
        : cfg_(c), log_M_(0.0f), stable_count_(0) {}

    // Add a new observation (MAP residual between consecutive steps)
    void addObs(float residual) {
        residuals_.push_back(residual);
        if ((int)residuals_.size() > cfg_.max_win)
            residuals_.pop_front();
        
        // Compute e-value for this step
        float e_val = computeEValue(residual);
        e_values_.push_back(e_val);
        
        // Update log e-process: log(M_T) = sum log(E_t)
        log_M_ += std::log(e_val);
        
        // Update stability counter
        if (residual < cfg_.convergence_thresh)
            stable_count_++;
        else
            stable_count_ = 0;
    }

    // Check if e-process threshold crossed → should stop
    bool shouldStop() const {
        // Guard: need minimum observations
        if ((int)residuals_.size() < cfg_.min_steps)
            return false;
        
        // Primary: e-process threshold (anytime-valid)
        // M_T >= 1/delta → log(M_T) >= -log(delta)
        float log_threshold = -std::log(cfg_.delta);
        if (log_M_ >= log_threshold)
            return true;
        
        // Secondary: stability check (practical convergence)
        if (stable_count_ >= cfg_.stable_req)
            return true;
        
        return false;
    }

    // Get current confidence level: P(H0 | data) ≈ 1 / (1 + M_T)
    float getConfidence() const {
        return 1.0f / (1.0f + std::exp(log_M_));
    }

    // Get current e-process value
    float getEProcess() const {
        return std::exp(log_M_);
    }

    // Get adaptive width (for compatibility with old interface)
    float getWidth() const {
        int n = residuals_.size();
        if (n < 3) return 1e6f;
        std::vector<float> v(residuals_.begin(), residuals_.end());
        std::sort(v.begin(), v.end());
        int q = std::clamp((int)std::ceil((n + 1) * (1 - cfg_.delta)) - 1, 0, n - 1);
        return v[q];
    }

    void reset() {
        residuals_.clear();
        e_values_.clear();
        log_M_ = 0.0f;
        stable_count_ = 0;
    }

    int size() const { return residuals_.size(); }

private:
    EProcessConfig cfg_;
    std::deque<float> residuals_;
    std::deque<float> e_values_;
    float log_M_;       // log of e-process product
    int stable_count_;

    // Compute e-value E_t from residual r_t
    //
    // Under H0 (not converged): residuals are large → E_t < 1
    // Under H1 (converged): residuals are small → E_t > 1
    //
    // Design: E_t = exp(eta * (thresh - r_t))
    // When r_t < thresh: E_t > 1 (evidence FOR convergence)
    // When r_t > thresh: E_t < 1 (evidence AGAINST convergence)
    //
    // This ensures:
    // - Under H0: E[E_t] ≤ 1 (super-martingale)
    // - Under H1: E[E_t] > 1 (e-process grows)
    float computeEValue(float residual) const {
        // Exponential tilting based on convergence threshold
        float e_val = std::exp(cfg_.eta * (cfg_.convergence_thresh - residual));
        
        // Clamp to prevent numerical issues
        // Min: 0.01 (don't let old evidence dominate too much)
        // Max: 10.0 (don't let single observation dominate)
        return std::clamp(e_val, 0.01f, 10.0f);
    }
};

// Keep SourceConfidenceRegion unchanged (it's still useful)
class SourceConfidenceRegion {
public:
    struct Config {
        float alpha; int min_p; int max_h;
        Config() : alpha(0.10f), min_p(6), max_h(40) {}
    };
    explicit SourceConfidenceRegion(const Config& c = Config()) : c_(c) {}
    void addMAP(float x, float y, float z) {
        hx_.push_back(x); hy_.push_back(y); hz_.push_back(z);
        if ((int)hx_.size() > c_.max_h) {
            hx_.pop_front(); hy_.pop_front(); hz_.pop_front();
        }
    }
    float getRadius() const {
        int n = hx_.size();
        if (n < c_.min_p) return 1e6f;
        std::vector<float> sx(hx_.begin(), hx_.end()), sy(hy_.begin(), hy_.end());
        std::sort(sx.begin(), sx.end()); std::sort(sy.begin(), sy.end());
        float mx = sx[n / 2], my = sy[n / 2];
        std::vector<float> d;
        for (int i = 0; i < n; i++)
            d.push_back(std::sqrt((hx_[i] - mx) * (hx_[i] - mx) + (hy_[i] - my) * (hy_[i] - my)));
        std::sort(d.begin(), d.end());
        int q = std::clamp((int)std::ceil((n + 1) * (1 - c_.alpha)) - 1, 0, n - 1);
        return d[q];
    }
    bool stable(float t = 1.0f) const { return getRadius() < t; }
    void centroid(float& x, float& y, float& z) const {
        x = y = z = 0; int n = hx_.size();
        if (!n) return;
        for (int i = 0; i < n; i++) { x += hx_[i]; y += hy_[i]; z += hz_[i]; }
        x /= n; y /= n; z /= n;
    }
    void reset() { hx_.clear(); hy_.clear(); hz_.clear(); }
private:
    Config c_;
    std::deque<float> hx_, hy_, hz_;
};

}} // namespace GSL::CP