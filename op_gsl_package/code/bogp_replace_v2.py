# -*- coding: utf-8 -*-
"""Replace ESC with BO+GP in OPGSL - robust version"""
import sys, re, os
sys.stdout.reconfigure(encoding='utf-8')

HPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp"
CPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"

# ============================================================
# HPP: Replace ESCState struct with GPState
# ============================================================
with open(HPP, "r") as f:
    hpp = f.read()

# Find the ESC block: from "// --- ESC" to "ESCState esc_;"
# This is a multi-line block
esc_start = hpp.find("// --- ESC (Extremum Seeking Control) ---")
esc_end = hpp.find("ESCState esc_;")
if esc_start < 0 or esc_end < 0:
    print(f"ERROR: Cannot find ESC block in HPP. start={esc_start} end={esc_end}")
    sys.exit(1)
esc_end += len("ESCState esc_;")

gp_struct = """// --- BO+GP (Bayesian Optimization with Gaussian Process, 2025) ---
    struct GPState {
        struct Obs { float z; float c; };
        std::deque<Obs> obs;
        int max_window = 50;
        float length_scale = 0.5f;
        float sigma_f = 1.0f;
        float sigma_n = 0.1f;
        float z_min = 0.0f;
        float z_max = 3.0f;
        std::vector<float> alpha_cache;
        std::vector<float> z_cache;
        bool cache_valid = false;

        void addObs(float z, float c) {
            obs.push_back({z, c});
            if ((int)obs.size() > max_window) obs.pop_front();
            cache_valid = false;
        }

        float kernel(float z1, float z2) const {
            float r = std::abs(z1 - z2);
            float s = std::sqrt(5.0f) * r / length_scale;
            return sigma_f * sigma_f * (1.0f + s + s * s / 3.0f) * std::exp(-s);
        }

        void fit() {
            int n = (int)obs.size();
            if (n < 2) { cache_valid = true; return; }
            z_cache.resize(n);
            std::vector<float> y(n);
            for (int i = 0; i < n; i++) { z_cache[i] = obs[i].z; y[i] = obs[i].c; }
            // Cholesky-free: direct Gaussian elimination for small n (<=50)
            std::vector<std::vector<float>> A(n, std::vector<float>(n + 1));
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < n; j++) {
                    A[i][j] = kernel(z_cache[i], z_cache[j]);
                    if (i == j) A[i][j] += sigma_n * sigma_n;
                }
                A[i][n] = y[i];
            }
            for (int col = 0; col < n; col++) {
                int pivot = col;
                for (int row = col + 1; row < n; row++)
                    if (std::abs(A[row][col]) > std::abs(A[pivot][col])) pivot = row;
                std::swap(A[col], A[pivot]);
                float diag = A[col][col];
                if (std::abs(diag) < 1e-10f) diag = 1e-10f;
                for (int j = col; j <= n; j++) A[col][j] /= diag;
                for (int row = 0; row < n; row++) {
                    if (row == col) continue;
                    float factor = A[row][col];
                    for (int j = col; j <= n; j++) A[row][j] -= factor * A[col][j];
                }
            }
            alpha_cache.resize(n);
            for (int i = 0; i < n; i++) alpha_cache[i] = A[i][n];
            cache_valid = true;
        }

        void predict(float z_star, float& mean, float& var) const {
            int n = (int)obs.size();
            if (n < 2) { mean = (n == 1) ? obs[0].c : 0.0f; var = sigma_f * sigma_f; return; }
            std::vector<float> k_star(n);
            for (int i = 0; i < n; i++) k_star[i] = kernel(z_star, z_cache[i]);
            mean = 0.0f;
            for (int i = 0; i < n; i++) mean += k_star[i] * alpha_cache[i];
            // Simplified variance (diagonal approximation for speed)
            float k_ss = kernel(z_star, z_star);
            float correction = 0.0f;
            for (int i = 0; i < n; i++) correction += k_star[i] * k_star[i] / (sigma_f * sigma_f + sigma_n * sigma_n);
            var = std::max(0.0f, k_ss - correction * sigma_f * sigma_f);
        }

        float getNextZ() {
            if (!cache_valid) fit();
            int n = (int)obs.size();
            if (n < 3) {
                static std::mt19937 rng(std::random_device{}());
                return std::uniform_real_distribution<float>(z_min, z_max)(rng);
            }
            int n_grid = 50;
            float best_z = (z_min + z_max) / 2.0f;
            float best_ucb = -1e30f;
            float beta = std::max(2.0f, 2.0f * std::log((float)n + 1.0f));
            for (int i = 0; i <= n_grid; i++) {
                float z = z_min + (z_max - z_min) * (float)i / (float)n_grid;
                float mu, var;
                predict(z, mu, var);
                float ucb = mu + std::sqrt(beta) * std::sqrt(std::max(0.0f, var));
                if (ucb > best_ucb) { best_ucb = ucb; best_z = z; }
            }
            return best_z;
        }

        void reset(float z_init, float z_lo, float z_hi) {
            obs.clear(); alpha_cache.clear(); z_cache.clear();
            cache_valid = false; z_min = z_lo; z_max = z_hi;
        }
    };
    GPState gp_;"""

hpp = hpp[:esc_start] + gp_struct + hpp[esc_end:]
hpp = hpp.replace("use_esc_altitude_", "use_gp_altitude_")
with open(HPP, "w") as f:
    f.write(hpp)
print("HPP: ESCState -> GPState OK")

# ============================================================
# CPP: Replace ESC logic with BO+GP
# ============================================================
with open(CPP, "r") as f:
    cpp = f.read()

# 1. Parameter name
cpp = cpp.replace('opgsl.altitude.esc', 'opgsl.altitude.gp')
cpp = cpp.replace('use_esc_altitude_', 'use_gp_altitude_')

# 2. Reset calls
cpp = cpp.replace("esc_.reset(0.3f, z_min_, z_max_);", "gp_.reset(0.3f, z_min_, z_max_);")
cpp = cpp.replace("esc_.reset(best_calibrated_z_, z_min_, z_max_);", "gp_.reset(best_calibrated_z_, z_min_, z_max_);")
cpp = cpp.replace("esc_.reset(current_altitude_, z_min_, z_max_);", "gp_.reset(current_altitude_, z_min_, z_max_);")

# 3. ESC residual update block (TRACK phase) - replace the whole block
# Find from "// ESC update in TRACK phase" to "esc_.update(...);"
esc_update_start = cpp.find("// ESC update in TRACK phase")
if esc_update_start >= 0:
    # Find the end: "esc_.update(std::max(0.0f, residual));"
    esc_update_end = cpp.find("esc_.update(", esc_update_start)
    if esc_update_end >= 0:
        esc_update_end = cpp.find(";", esc_update_end) + 1
        gp_update = """// BO+GP: add observation to Gaussian Process
    if (alt_phase_ == AltPhase::TRACK && use_gp_altitude_) {
        gp_.addObs(current_altitude_, latest_gas_);
    }"""
        cpp = cpp[:esc_update_start] + gp_update + cpp[esc_update_end:]
        print("CPP: ESC residual block -> GP addObs OK")
    else:
        print("WARN: Could not find esc_.update call")
else:
    print("WARN: Could not find ESC update block")

# 4. Replace esc_.getZ() with gp_.getNextZ()
cpp = cpp.replace("esc_.getZ()", "gp_.getNextZ()")

# 5. Replace ESC log values
cpp = cpp.replace("esc_.amplitude, esc_.G_hat,", "0.0f, 0.0f,")
cpp = cpp.replace("OPGSL-3D: phase={} z={:.2f} esc_z={:.2f}", "OPGSL-3D: phase={} z={:.2f} gp_z={:.2f}")

# 6. Any remaining esc_ references
remaining = [i for i in range(len(cpp)) if cpp[i:i+4] == "esc_"]
if remaining:
    for pos in remaining:
        ctx = cpp[max(0,pos-20):pos+30]
        print(f"WARN: remaining esc_ at pos {pos}: ...{ctx}...")
    # Replace any straggler
    cpp = cpp.replace("esc_.", "gp_.")

with open(CPP, "w") as f:
    f.write(cpp)
print("CPP: ESC -> GP OK")

# ============================================================
# Verify
# ============================================================
with open(CPP, "r") as f:
    v = f.read()
with open(HPP, "r") as f:
    vh = f.read()

print("\n=== Verification ===")
for needle, label in [("gp_.addObs", "GP addObs"), ("gp_.getNextZ", "GP getNextZ"),
                       ("gp_.reset", "GP reset"), ("use_gp_altitude_", "GP toggle"),
                       ("opgsl.altitude.gp", "GP param")]:
    print(f"  CPP {'OK' if needle in v else 'MISS'} {label}")

for needle, label in [("GPState gp_;", "GP struct"), ("struct GPState", "GP struct def"),
                       ("use_gp_altitude_", "GP toggle")]:
    print(f"  HPP {'OK' if needle in vh else 'MISS'} {label}")

for remnant in ["esc_.", "ESCState", "use_esc_altitude_", "opgsl.altitude.esc"]:
    in_cpp = remnant in v
    in_hpp = remnant in vh
    if in_cpp: print(f"  WARN: ESC remnant '{remnant}' in CPP!")
    if in_hpp: print(f"  WARN: ESC remnant '{remnant}' in HPP!")

print("\nDone! Build with: cd /home/zyc/gsl_ws && source /opt/ros/humble/setup.bash && source install/setup.bash && colcon build --packages-select gsl_server")
