# -*- coding: utf-8 -*-
"""Replace ESC with BO+GP in OPGSL code"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

HPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp"
CPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"

with open(HPP, "r") as f:
    hpp = f.read()
with open(CPP, "r") as f:
    cpp = f.read()

# ============================================================
# HPP: Replace ESCState with GPState
# ============================================================
# Find and replace the entire ESCState struct
esc_pattern = r'// --- ESC.*?ESCState esc_;'
gp_replacement = """// --- BO+GP (Bayesian Optimization with Gaussian Process) ---
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

hpp_new = re.sub(esc_pattern, gp_replacement, hpp, flags=re.DOTALL)
if hpp_new != hpp:
    hpp = hpp_new
    print("HPP: ESCState -> GPState OK")
else:
    print("HPP: Pattern not found, trying line-by-line...")
    # Fallback: replace key lines
    hpp = hpp.replace("ESCState esc_;", "GPState gp_;")

# Replace all use_esc_altitude_ with use_gp_altitude_
hpp = hpp.replace("use_esc_altitude_", "use_gp_altitude_")
hpp = hpp.replace("bool use_esc_altitude_", "bool use_gp_altitude_")

with open(HPP, "w") as f:
    f.write(hpp)

# ============================================================
# CPP: Replace ESC logic with BO+GP
# ============================================================

# Parameter name
cpp = cpp.replace("opgsl.altitude.esc", "opgsl.altitude.gp")
cpp = cpp.replace("use_esc_altitude_", "use_gp_altitude_")

# Reset calls
cpp = cpp.replace("esc_.reset(0.3f, z_min_, z_max_);", "gp_.reset(0.3f, z_min_, z_max_);")
cpp = cpp.replace("esc_.reset(current_altitude_, z_min_, z_max_);", "gp_.reset(current_altitude_, z_min_, z_max_);")
cpp = cpp.replace("esc_.reset(best_calibrated_z_, z_min_, z_max_);", "gp_.reset(best_calibrated_z_, z_min_, z_max_);")

# Replace ESC residual update block
esc_block_pattern = r'// Residual-based ESC.*?esc_.update([^)]+);'
gp_block = '// BO+GP: add observation to Gaussian Process\n    if (alt_phase_ == AltPhase::TRACK && use_gp_altitude_) {\n        gp_.addObs(current_altitude_, latest_gas_);\n    }'
cpp = re.sub(esc_block_pattern, gp_block, cpp, flags=re.DOTALL)

# Simple fallback for esc_.update
cpp = cpp.replace("esc_.update(latest_gas_);", "gp_.addObs(current_altitude_, latest_gas_);")
cpp = cpp.replace("esc_.update(std::max(0.0f, residual));", "gp_.addObs(current_altitude_, latest_gas_);")

# Replace esc_.getZ() with gp_.getNextZ()
cpp = cpp.replace("esc_.getZ()", "gp_.getNextZ()")

# Replace ESC-related log values
cpp = cpp.replace("esc_.amplitude, esc_.G_hat,", "0.0f, 0.0f,")

# Fix log format string
cpp = cpp.replace("OPGSL-3D: phase={} z={:.2f} esc_z={:.2f}", "OPGSL-3D: phase={} z={:.2f} gp_z={:.2f}")

with open(CPP, "w") as f:
    f.write(cpp)

# ============================================================
# Verify
# ============================================================
with open(CPP, "r") as f:
    v = f.read()
with open(HPP, "r") as f:
    vh = f.read()

print("\n=== Verification ===")
checks_cpp = [
    ("gp_.addObs", "GP addObs"),
    ("gp_.getNextZ", "GP getNextZ"),
    ("gp_.reset", "GP reset"),
    ("use_gp_altitude_", "GP toggle"),
    ("opgsl.altitude.gp", "GP param"),
]
for needle, label in checks_cpp:
    print(f"  CPP {'OK' if needle in v else 'MISS'} {label}")

checks_hpp = [
    ("GPState gp_;", "GP struct"),
    ("struct GPState", "GP struct def"),
    ("use_gp_altitude_", "GP toggle"),
]
for needle, label in checks_hpp:
    print(f"  HPP {'OK' if needle in vh else 'MISS'} {label}")

# Check no ESC remnants
for remnant in ["esc_.", "ESCState", "use_esc_altitude_", "opgsl.altitude.esc"]:
    if remnant in v:
        print(f"  WARN: ESC remnant '{remnant}' in CPP!")
    if remnant in vh:
        print(f"  WARN: ESC remnant '{remnant}' in HPP!")

print("\nDone!")
