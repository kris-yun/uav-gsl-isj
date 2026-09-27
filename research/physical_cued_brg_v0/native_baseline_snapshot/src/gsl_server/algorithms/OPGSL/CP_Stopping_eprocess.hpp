#pragma once
#include <deque>
#include <vector>
#include <algorithm>
#include <cmath>
#include <numeric>
#include <limits>

namespace GSL { namespace CP {

// =========================================================================
//  E-Process Stopping Rule - v2 (Hoeffding super-martingale)
//
//  Anytime-valid inference via e-processes.
//  Reference: Ramdas et al. (2023) Game-theoretic Statistics and Safe
//             Anytime-Valid Inference. Statistical Science 38(4).
//             DOI:10.1214/23-sts894
//
//  Key property (Ville inequality):
//      P( sup_T M_T >= 1/delta ) <= delta
//  for ANY stopping time T, provided M_t is a super-martingale
//  under H0 with M_0 = 1.
//
//  v2 fixes over v1:
//  - Hoeffding e-value: E_t = exp(eta*x_t - eta^2*B^2/2) where x_t is
//    the bounded score and B the half-width.  This guarantees E[E_t|H0] <= 1
//    whenever E[x_t|H0] <= 0 (i.e., E[residual] >= thresh under H0).
//  - Warmup period: no evidence accumulation during posterior burn-in.
//  - Higher min_steps and stable_req to prevent premature triggers.
//  - Explicit post-warmup counter so warmup does not count toward min_steps.
// =========================================================================

struct EProcessConfig {
    float delta;               // Significance level (e.g. 0.10 -> 90 pct conf)
    int   min_steps;           // Min post-warmup observations before stopping
    int   max_win;             // Max sliding-window size for residual history
    float convergence_thresh;  // Residual threshold converged (meters)
    int   stable_req;          // Consecutive stable post-warmup steps required
    float eta;                 // Hoeffding tilting parameter (learning rate)
    float decay;               // Discount on log-M (1.0 = strict e-process)
    int   warmup_steps;        // Steps before e-process starts accumulating

    EProcessConfig()
        : delta(0.10f)
        , min_steps(20)
        , max_win(50)
        , convergence_thresh(1.5f)
        , stable_req(8)
        , eta(0.40f)
        , decay(1.0f)          // 1.0 = strict anytime-valid; <1.0 = discounted
        , warmup_steps(10)
    {}
};

class EProcessStopping {
public:
    explicit EProcessStopping(const EProcessConfig& c = EProcessConfig())
        : cfg_(c)
        , log_M_(0.0f)
        , stable_count_(0)
        , post_warmup_count_(0)
    {
        // Pre-compute Hoeffding penalty: psi = eta^2 * B^2 / 2
        // where B = convergence_thresh is the half-width of the bounded score.
        //
        // x_t = clamp(thresh - r_t, -B, B)  in [-B, B]
        // Hoeffding lemma: E[exp(eta*x)] <= exp(eta^2 * (2B)^2 / 8)
        //                                  = exp(eta^2 * B^2 / 2) = exp(psi)
        float B = cfg_.convergence_thresh;
        psi_ = 0.5f * cfg_.eta * cfg_.eta * B * B;
    }

    // -----------------------------------------------------------------
    //  Add a new observation (MAP residual between consecutive steps)
    // -----------------------------------------------------------------
    void addObs(float residual) {
        // Guard: ignore NaN / Inf
        if (!std::isfinite(residual))
            return;

        residuals_.push_back(residual);
        if ((int)residuals_.size() > cfg_.max_win)
            residuals_.pop_front();

        // ---- Warmup phase: no evidence accumulation ----
        // The posterior needs time to burn in; early MAP positions
        // can be deceptively stable (diffuse posterior, few observations).
        if ((int)residuals_.size() <= cfg_.warmup_steps) {
            e_values_.push_back(1.0f);
            if ((int)e_values_.size() > cfg_.max_win)
                e_values_.pop_front();
            return;
        }

        // ---- Post-warmup phase ----
        post_warmup_count_++;

        // Update stability counter (only post-warmup)
        if (residual < cfg_.convergence_thresh)
            stable_count_++;
        else
            stable_count_ = 0;

        // Compute Hoeffding e-value
        float e_val = computeEValue(residual);
        e_values_.push_back(e_val);
        if ((int)e_values_.size() > cfg_.max_win)
            e_values_.pop_front();

        // Update log e-process:
        //   decay = 1.0 : log M_t = log M_{t-1} + log E_t  (strict e-process)
        //   decay < 1.0 : log M_t = decay*log M_{t-1} + log E_t  (discounted)
        // Discounted form is NOT a strict e-process but is more robust
        // when the stationarity assumption of H0 may be violated.
        log_M_ = cfg_.decay * log_M_ + std::log(e_val);
    }

    // -----------------------------------------------------------------
    //  Check if stopping criterion is met
    // -----------------------------------------------------------------
    bool shouldStop() const {
        // Guard: need minimum post-warmup observations
        if (post_warmup_count_ < cfg_.min_steps)
            return false;

        // Primary: e-process threshold (anytime-valid)
        // M_t >= 1/delta  <=>  log M_t >= -log(delta)
        float log_threshold = -std::log(cfg_.delta);
        if (log_M_ >= log_threshold)
            return true;

        // Secondary: sustained stability (consecutive post-warmup steps)
        if (stable_count_ >= cfg_.stable_req)
            return true;

        return false;
    }

    // Approximate posterior probability: P(H0 | data) ~ 1/(1 + M_t)
    float getConfidence() const {
        float M = std::exp(log_M_);
        return 1.0f / (1.0f + M);
    }

    // Current e-process value M_t
    float getEProcess() const {
        return std::exp(log_M_);
    }

    // Adaptive width for compatibility with old interface
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
        post_warmup_count_ = 0;
    }

    int size() const { return residuals_.size(); }
    int postWarmupCount() const { return post_warmup_count_; }

private:
    EProcessConfig cfg_;
    std::deque<float> residuals_;
    std::deque<float> e_values_;
    float log_M_;           // log of (discounted) e-process
    int   stable_count_;    // consecutive post-warmup stable steps
    int   post_warmup_count_;
    float psi_;             // pre-computed Hoeffding penalty

    // -----------------------------------------------------------------
    //  Hoeffding e-value for bounded score
    //
    //  Score:  x_t = clamp( thresh - r_t,  -thresh,  thresh )
    //    r_t < thresh  =>  x_t > 0   (convergence evidence)
    //    r_t = thresh  =>  x_t = 0   (neutral)
    //    r_t > thresh  =>  x_t < 0   (evidence against)
    //
    //  E-value:  E_t = exp( eta * x_t  -  eta^2 * B^2 / 2 )
    //
    //  Super-martingale guarantee (Hoeffding lemma):
    //    For bounded X in [-B, B]:
    //      E[exp(eta * X)]  <=  exp(eta^2 * (2B)^2 / 8)
    //                        =  exp(eta^2 * B^2 / 2)
    //    Therefore, if E[x_t|H0] <= 0:
    //      E[E_t|H0] = E[exp(eta*x_t - psi)] <= exp(psi - psi) = 1
    //
    //  Per-step log contribution bounded by: eta*B - psi = eta*B*(1 - eta/2)
    //  With eta=0.4, B=1.5: max log = 0.48 -> need >= 5 perfect post-warmup
    //  steps.  With min_steps=20, warmup=10: total >= 20.
    //
    //  The neutral residual (E_t = 1 exactly) occurs at:
    //    x_t = psi/eta = eta*B^2/2  ->  r_neutral = thresh - eta*thresh^2/2
    //  With eta=0.4, thresh=1.5:  r_neutral = 1.5 - 0.45 = 1.05 m
    //  Residuals above 1.05 m provide evidence AGAINST convergence.
    // -----------------------------------------------------------------
    float computeEValue(float residual) const {
        float B = cfg_.convergence_thresh;
        float x_t = std::clamp(B - residual, -B, B);
        float log_e = cfg_.eta * x_t - psi_;
        return std::exp(log_e);
    }
};

// =========================================================================
//  SourceConfidenceRegion  (unchanged)
// =========================================================================
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
