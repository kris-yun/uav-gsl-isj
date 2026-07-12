#pragma once
// =========================================================================
//  SPRT Stopping Rule (Wald 1945)
//
//  Sequential Probability Ratio Test for MAP residual convergence.
//  Replaces the ad-hoc "stable_count" with a theoretically optimal
//  sequential test.
//
//  Model: MAP inter-step residuals r_t ~ Exponential(lambda)
//    H0 (unconverged):  mean r0 (e.g. 2.0 m)
//    H1 (converged):    mean r1 (e.g. 0.3 m)
//
//  Log-likelihood ratio per observation:
//    LLR_t = ln(r0/r1) + (1/r0 - 1/r1) * r_t
//
//  Cumulative LLR: S_t = sum(LLR_k)
//  Stop and accept H1 when S_t >= A = ln((1-beta)/alpha)
//  Stop and accept H0 when S_t <= B = ln(beta/(1-alpha))
//  Continue otherwise.
//
//  Wald-Wolfowitz optimality theorem:
//    SPRT minimizes E[N|H0] and E[N|H1] among all sequential tests
//    achieving the same (alpha, beta) error probabilities.
//
//  References:
//    Wald, A. (1945). Sequential tests of statistical hypotheses.
//      Annals of Mathematical Statistics, 16(2), 117-186.
//    Wald, A. and Wolfowitz, J. (1948). Optimum character of the
//      sequential probability ratio test. Annals of Mathematical
//      Statistics, 19(3), 326-339.
// =========================================================================

#include <deque>
#include <cmath>
#include <algorithm>

namespace GSL { namespace CP {

struct SPRTConfig {
    float r0_mean;          // Unconverged mean residual (meters)
    float r1_mean;          // Converged mean residual (meters)
    float alpha;            // False positive rate (declare converged when not)
    float beta;             // False negative rate (miss convergence when real)
    int   warmup_steps;     // Steps before SPRT accumulates (posterior burn-in)
    int   min_steps;        // Minimum post-warmup observations before stopping
    int   max_win;          // Max history window

    SPRTConfig()
        : r0_mean(2.0f)     // H0: MAP jumps ~2m between steps
        , r1_mean(0.3f)     // H1: MAP stable ~0.3m between steps
        , alpha(0.05f)      // 5% false convergence
        , beta(0.10f)       // 10% missed convergence
        , warmup_steps(10)
        , min_steps(8)
        , max_win(100)
    {}
};

class SPRTStopping {
public:
    explicit SPRTStopping(const SPRTConfig& c = SPRTConfig())
        : cfg_(c)
        , cumulative_llr_(0.0f)
        , post_warmup_count_(0)
    {
        lambda0_ = 1.0f / cfg_.r0_mean;
        lambda1_ = 1.0f / cfg_.r1_mean;
        llr_constant_ = std::log(cfg_.r0_mean / cfg_.r1_mean);
        upper_boundary_ = std::log((1.0f - cfg_.beta) / cfg_.alpha);
        lower_boundary_ = std::log(cfg_.beta / (1.0f - cfg_.alpha));
        neutral_residual_ = llr_constant_ / (lambda1_ - lambda0_);
    }

    void addObs(float residual) {
        if (!std::isfinite(residual))
            return;
        residuals_.push_back(residual);
        if ((int)residuals_.size() > cfg_.max_win)
            residuals_.pop_front();
        if ((int)residuals_.size() <= cfg_.warmup_steps)
            return;
        post_warmup_count_++;
        // LLR_t = ln(r0/r1) + (1/r0 - 1/r1) * r_t
        float llr_t = llr_constant_ + (lambda0_ - lambda1_) * residual;
        cumulative_llr_ += llr_t;
    }

    // +1 = converged, -1 = not converged, 0 = continue
    int checkStopping() const {
        if (post_warmup_count_ < cfg_.min_steps)
            return 0;
        if (cumulative_llr_ >= upper_boundary_)
            return 1;
        if (cumulative_llr_ <= lower_boundary_)
            return -1;
        return 0;
    }

    float getCumulativeLLR() const { return cumulative_llr_; }
    float getUpperBoundary() const { return upper_boundary_; }
    float getLowerBoundary() const { return lower_boundary_; }
    float getNeutralResidual() const { return neutral_residual_; }
    int   postWarmupCount() const { return post_warmup_count_; }
    int   size() const { return residuals_.size(); }

    float getRecentMean(int n = 10) const {
        int sz = std::min(n, (int)residuals_.size());
        if (sz <= 0) return 1e6f;
        float sum = 0;
        auto it = residuals_.end() - sz;
        for (; it != residuals_.end(); ++it) sum += *it;
        return sum / sz;
    }

    void reset() {
        residuals_.clear();
        cumulative_llr_ = 0.0f;
        post_warmup_count_ = 0;
    }

private:
    SPRTConfig cfg_;
    float lambda0_, lambda1_;
    float llr_constant_;
    float upper_boundary_, lower_boundary_;
    float neutral_residual_;
    float cumulative_llr_;
    int   post_warmup_count_;
    std::deque<float> residuals_;
};

}} // namespace GSL::CP
