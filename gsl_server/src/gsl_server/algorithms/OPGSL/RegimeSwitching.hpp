#pragma once
// Regime-Switching Observation Model (RS-OM)
// Source Domain: Econometrics - Hamilton (1989) Markov Regime-Switching
// Novel in GSL: No existing work uses regime-switching for plume observation modeling
//
// Core Idea: Gas detection is NOT binary (hit/no-hit) but a 3-state regime process:
//   State 1: Clear air (no gas, low variance)
//   State 2: Plume filament (intermittent gas, high variance)
//   State 3: Near source (persistent high gas, moderate variance)
//
// Each regime has a distinct observation likelihood:
//   S=1: z ~ N(0, sigma_bg^2)           -- background noise
//   S=2: z ~ Exp(lambda) + noise         -- intermittent filament encounters
//   S=3: z ~ LogNormal(mu_src, sigma^2)  -- sustained source proximity
//
// The regime transitions follow a Markov chain:
//   P(S_t = j | S_{t-1} = i) = p_ij
//
// Key advantage over fixed threshold: CUSUM-BCD uses a single threshold, but
// regime-switching provides PROBABILISTIC regime classification, allowing
// the posterior update to weight observations by regime confidence.
//
// Mathematical Foundation:
//   Hamilton Filter: P(S_t=k|z_{1:t}) ¡Ø f(z_t|S_t=k) * ¦²_i p_ik * P(S_{t-1}=i|z_{1:t-1})
//   This is the EXACT posterior over regimes given all observations.
//
// Reference: Hamilton (1989) "A New Approach to the Economic Analysis of Nonstationary Time Series"

#include <cmath>
#include <array>
#include <algorithm>
#include <numeric>

namespace GSL {
namespace Innovation {

class RegimeSwitching {
public:
    static constexpr int N_REGIMES = 3;
    enum Regime { CLEAR = 0, FILAMENT = 1, NEAR_SOURCE = 2 };

    struct Config {
        // Observation model parameters
        double sigma_bg = 0.02;           // Background noise std
        double lambda_filament = 2.0;     // Filament exponential rate
        double mu_src = 0.5;             // Log-normal mean for near-source
        double sigma_src = 0.3;          // Log-normal std for near-source

        // Transition matrix (rows: from, cols: to)
        // Default: high self-transition (regime persistence)
        double p_stay_clear = 0.85;
        double p_stay_filament = 0.70;
        double p_stay_near = 0.80;
        double p_clear_to_filament = 0.12;
        double p_filament_to_near = 0.20;
        double p_filament_to_clear = 0.10;
        double p_near_to_filament = 0.15;
        double p_near_to_clear = 0.05;

        // Prior
        double prior_clear = 0.7;
        double prior_filament = 0.2;
        double prior_near = 0.1;

        // Adaptation
        double learning_rate = 0.02;      // Online parameter adaptation rate
        int min_samples_adapt = 20;       // Min samples before adapting params
    };

    struct RSResult {
        std::array<double, N_REGIMES> regime_probs;  // P(S_t=k|z_{1:t})
        Regime most_likely_regime;
        double gas_confidence;        // P(S_t ¡Ê {FILAMENT, NEAR_SOURCE})
        double regime_entropy;        // Entropy of regime distribution
        double observation_weight;    // Weight for posterior update [0,1]
        double log_likelihood;        // Total log-likelihood
        bool is_adapted;              // Whether online adaptation is active
    };

    void init(const Config& cfg) {
        cfg_ = cfg;

        // Initialize transition matrix
        P_trans_[CLEAR][CLEAR] = cfg.p_stay_clear;
        P_trans_[CLEAR][FILAMENT] = cfg.p_clear_to_filament;
        P_trans_[CLEAR][NEAR_SOURCE] = 1.0 - cfg.p_stay_clear - cfg.p_clear_to_filament;

        P_trans_[FILAMENT][CLEAR] = cfg.p_filament_to_clear;
        P_trans_[FILAMENT][FILAMENT] = cfg.p_stay_filament;
        P_trans_[FILAMENT][NEAR_SOURCE] = cfg.p_filament_to_near;

        P_trans_[NEAR_SOURCE][CLEAR] = cfg.p_near_to_clear;
        P_trans_[NEAR_SOURCE][FILAMENT] = cfg.p_near_to_filament;
        P_trans_[NEAR_SOURCE][NEAR_SOURCE] = cfg.p_stay_near;

        // Initialize regime probabilities (prior)
        regime_probs_[CLEAR] = cfg.prior_clear;
        regime_probs_[FILAMENT] = cfg.prior_filament;
        regime_probs_[NEAR_SOURCE] = cfg.prior_near;

        n_samples_ = 0;
        n_adapted_ = 0;
        result_ = RSResult();
    }

    RSResult update(double gas_reading, double wind_speed) {
        n_samples_++;

        // Step 1: Compute observation likelihoods f(z_t | S_t = k)
        std::array<double, N_REGIMES> obs_likelihoods;

        // Regime 1: Clear air - z ~ N(0, sigma_bg^2)
        obs_likelihoods[CLEAR] = gaussian_pdf(gas_reading, 0.0, cfg_.sigma_bg);

        // Regime 2: Plume filament - z ~ Exp(lambda) for z > threshold, else noise
        if (gas_reading > cfg_.sigma_bg * 2) {
            obs_likelihoods[FILAMENT] = cfg_.lambda_filament * std::exp(-cfg_.lambda_filament * gas_reading);
            // Add Gaussian component for noise
            obs_likelihoods[FILAMENT] += 0.3 * gaussian_pdf(gas_reading, 0.0, cfg_.sigma_bg);
        } else {
            obs_likelihoods[FILAMENT] = 0.3 * gaussian_pdf(gas_reading, 0.0, cfg_.sigma_bg);
        }

        // Regime 3: Near source - z ~ LogNormal(mu_src, sigma_src^2)
        if (gas_reading > 1e-6) {
            double log_z = std::log(gas_reading + 1e-10);
            obs_likelihoods[NEAR_SOURCE] = lognormal_pdf(log_z, cfg_.mu_src, cfg_.sigma_src);
        } else {
            obs_likelihoods[NEAR_SOURCE] = 1e-6;
        }

        // Step 2: Hamilton Filter update
        // P(S_t=k|z_{1:t}) ¡Ø f(z_t|S_t=k) * ¦²_i p_ik * P(S_{t-1}=i|z_{1:t-1})
        std::array<double, N_REGIMES> predicted;
        for (int k = 0; k < N_REGIMES; ++k) {
            predicted[k] = 0.0;
            for (int i = 0; i < N_REGIMES; ++i) {
                predicted[k] += P_trans_[i][k] * regime_probs_[i];
            }
        }

        // Multiply by observation likelihood
        double total = 0.0;
        for (int k = 0; k < N_REGIMES; ++k) {
            regime_probs_[k] = obs_likelihoods[k] * predicted[k];
            total += regime_probs_[k];
        }

        // Normalize
        if (total > 0) {
            for (int k = 0; k < N_REGIMES; ++k) {
                regime_probs_[k] /= total;
            }
        }

        // Clamp to avoid numerical issues
        for (int k = 0; k < N_REGIMES; ++k) {
            regime_probs_[k] = std::max(1e-10, std::min(1.0 - 1e-10, regime_probs_[k]));
        }

        // Step 3: Online parameter adaptation (stochastic EM)
        if (n_samples_ >= cfg_.min_samples_adapt) {
            adaptParameters(gas_reading);
        }

        // Compute result
        result_.regime_probs = regime_probs_;
        result_.most_likely_regime = static_cast<Regime>(
            std::distance(regime_probs_.begin(),
                         std::max_element(regime_probs_.begin(), regime_probs_.end())));

        result_.gas_confidence = regime_probs_[FILAMENT] + regime_probs_[NEAR_SOURCE];

        // Regime entropy
        result_.regime_entropy = 0.0;
        for (int k = 0; k < N_REGIMES; ++k) {
            if (regime_probs_[k] > 1e-10) {
                result_.regime_entropy -= regime_probs_[k] * std::log(regime_probs_[k]);
            }
        }

        // Observation weight: how much to trust this observation for posterior update
        // High confidence in FILAMENT/NEAR_SOURCE -> high weight
        // High entropy (uncertain regime) -> low weight
        double max_entropy = std::log(N_REGIMES);
        result_.observation_weight = result_.gas_confidence * (1.0 - result_.regime_entropy / max_entropy);
        result_.observation_weight = std::max(0.01, std::min(1.0, result_.observation_weight));

        result_.log_likelihood = std::log(total + 1e-10);
        result_.is_adapted = (n_adapted_ > 0);

        return result_;
    }

    // Get regime-specific likelihood for external use
    double getRegimeLikelihood(int regime, double gas_reading) const {
        switch (regime) {
            case CLEAR: return gaussian_pdf(gas_reading, 0.0, cfg_.sigma_bg);
            case FILAMENT: return cfg_.lambda_filament * std::exp(-cfg_.lambda_filament * gas_reading);
            case NEAR_SOURCE: return lognormal_pdf(std::log(gas_reading + 1e-10), cfg_.mu_src, cfg_.sigma_src);
            default: return 0.0;
        }
    }

    const RSResult& result() const { return result_; }

private:
    double gaussian_pdf(double x, double mu, double sigma) const {
        double z = (x - mu) / sigma;
        return std::exp(-0.5 * z * z) / (sigma * std::sqrt(2.0 * M_PI));
    }

    double lognormal_pdf(double log_x, double mu, double sigma) const {
        double z = (log_x - mu) / sigma;
        return std::exp(-0.5 * z * z) / (std::exp(log_x) * sigma * std::sqrt(2.0 * M_PI));
    }

    void adaptParameters(double gas_reading) {
        // Online stochastic EM: update observation parameters
        double lr = cfg_.learning_rate;

        // Update filament lambda (exponential rate)
        if (regime_probs_[FILAMENT] > 0.3 && gas_reading > 0.01) {
            double new_lambda = 1.0 / (gas_reading + 1e-6);
            cfg_.lambda_filament = (1.0 - lr) * cfg_.lambda_filament + lr * new_lambda;
            cfg_.lambda_filament = std::max(0.5, std::min(10.0, cfg_.lambda_filament));
        }

        // Update near-source log-normal parameters
        if (regime_probs_[NEAR_SOURCE] > 0.3 && gas_reading > 0.01) {
            double log_z = std::log(gas_reading + 1e-10);
            cfg_.mu_src = (1.0 - lr) * cfg_.mu_src + lr * log_z;
            double diff = log_z - cfg_.mu_src;
            cfg_.sigma_src = (1.0 - lr) * cfg_.sigma_src + lr * std::abs(diff);
            cfg_.sigma_src = std::max(0.1, std::min(1.0, cfg_.sigma_src));
        }

        n_adapted_++;
    }

    Config cfg_;
    std::array<std::array<double, N_REGIMES>, N_REGIMES> P_trans_;
    std::array<double, N_REGIMES> regime_probs_;
    RSResult result_;
    int n_samples_ = 0;
    int n_adapted_ = 0;
};

} // namespace Innovation
} // namespace GSL
