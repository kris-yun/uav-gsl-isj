// WindEvidenceModule.h — Single-file M1: Wind Evidence Modulation.
//
// Interface:
//   WindEvidenceModule::Config config;
//   config.u0 = <from calibration>;
//   config.beta0 = <from calibration>;
//   config.beta_d = <from calibration>;
//   config.beta_up = <from calibration>;
//
//   WindEvidenceModule mod(config);
//
//   // Each StopAndMeasure block:
//   mod.beginBlock();
//   mod.addWindSample(ux, uy);  // called N times per block
//   mod.endBlock();
//
//   // For each candidate:
//   double q_iso = <base isotropic q>;
//   double q_final = mod.apply(q_iso, sensor_x, sensor_y, sensor_z,
//                               cand_x, cand_y, cand_z);
//
// When disabled: apply() returns q_iso unchanged.

#pragma once

#include <cmath>
#include <algorithm>

namespace GSL {

struct WindEvidenceConfig {
    double u0 = 0.10;      // wind speed scale (from calibration, NOT from error)
    double beta0 = 0.0;    // directional kernel intercept
    double beta_d = 0.0;   // distance decay in directional kernel
    double beta_up = 1.0;  // upwind penalty (>= 0)
    bool enabled = true;   // false => apply() returns q_iso unchanged
};

class WindEvidenceModule {
public:
    explicit WindEvidenceModule(const WindEvidenceConfig& cfg) : cfg_(cfg) {}

    // --- Per-block lifecycle ---

    void beginBlock() {
        sum_ux_ = 0.0;
        sum_uy_ = 0.0;
        sum_speed_ = 0.0;
        n_ = 0;
    }

    void addWindSample(double ux, double uy) {
        sum_ux_ += ux;
        sum_uy_ += uy;
        sum_speed_ += std::hypot(ux, uy);
        ++n_;
    }

    void endBlock() {
        if (n_ > 0) {
            mean_ux_ = sum_ux_ / static_cast<double>(n_);
            mean_uy_ = sum_uy_ / static_cast<double>(n_);
            mean_speed_ = sum_speed_ / static_cast<double>(n_);
        } else {
            mean_ux_ = 0.0;
            mean_uy_ = 0.0;
            mean_speed_ = 0.0;
        }
        U_ = std::hypot(mean_ux_, mean_uy_);
        R_ = (mean_speed_ > 1e-12) ? U_ / mean_speed_ : 0.0;
        rho_ = (U_ + cfg_.u0 > 1e-12)
             ? R_ * U_ / (U_ + cfg_.u0)
             : 0.0;
    }

    // --- Per-candidate prediction ---

    // q_base: isotropic base q (from B0)
    // Returns: q_M1 = (1-rho)*q_iso + rho*q_dir, or q_base if disabled.
    double apply(double q_iso,
                 double sensor_x, double sensor_y, double sensor_z,
                 double cand_x,   double cand_y,   double cand_z) const {
        if (!cfg_.enabled || n_ < 1 || rho_ < 1e-12) {
            return q_iso;
        }

        // Directional kernel
        const double dx = sensor_x - cand_x;
        const double dy = sensor_y - cand_y;
        const double dz = sensor_z - cand_z;
        const double dist = std::hypot(std::hypot(dx, dy), dz);

        // a = dot(r, u_hat): positive when sensor is downwind of source
        const double a = (U_ > 1e-12)
            ? (dx * mean_ux_ + dy * mean_uy_) / U_
            : 0.0;
        const double a_up = std::max(-a, 0.0);  // upwind component

        const double logit = cfg_.beta0
                           - cfg_.beta_d * dist
                           - cfg_.beta_up * a_up;
        const double q_dir = sigmoid(logit);

        return (1.0 - rho_) * q_iso + rho_ * q_dir;
    }

    // --- Accessors ---

    double rho() const { return rho_; }
    double U() const { return U_; }
    double R() const { return R_; }
    int sampleCount() const { return n_; }
    double meanUx() const { return mean_ux_; }
    double meanUy() const { return mean_uy_; }

private:
    WindEvidenceConfig cfg_;

    // Accumulator
    double sum_ux_ = 0.0;
    double sum_uy_ = 0.0;
    double sum_speed_ = 0.0;
    int n_ = 0;

    // Block stats (set by endBlock)
    double mean_ux_ = 0.0;
    double mean_uy_ = 0.0;
    double mean_speed_ = 0.0;
    double U_ = 0.0;
    double R_ = 0.0;
    double rho_ = 0.0;

    static double sigmoid(double x) {
        if (x >= 0.0) { const double z = std::exp(-x); return 1.0 / (1.0 + z); }
        const double z = std::exp(x); return z / (1.0 + z);
    }
};

}  // namespace GSL
