# -*- coding: utf-8 -*-
"""Surgical ESC -> BO+GP replacement using exact line matching"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

HPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp"
CPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"

# ============================================================
# HPP: Replace ESCState block with GPState
# ============================================================
with open(HPP, "r") as f:
    hpp_lines = f.readlines()

# Find ESC block boundaries
esc_start = None
esc_end = None
for i, line in enumerate(hpp_lines):
    if "// --- ESC (Extremum Seeking Control) ---" in line:
        esc_start = i
    if "ESCState esc_;" in line:
        esc_end = i
        break

if esc_start is None or esc_end is None:
    print(f"ERROR: Cannot find ESC block. start={esc_start} end={esc_end}")
    sys.exit(1)

print(f"HPP: Replacing lines {esc_start+1}-{esc_end+1} (ESCState -> GPState)")

gp_block = """// --- BO+GP (Bayesian Optimization with Gaussian Process, 2025) ---
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
    GPState gp_;
"""

hpp_lines_new = hpp_lines[:esc_start] + [gp_block] + hpp_lines[esc_end+1:]
hpp_text = "".join(hpp_lines_new)
hpp_text = hpp_text.replace("use_esc_altitude_", "use_gp_altitude_")
with open(HPP, "w") as f:
    f.write(hpp_text)
print("HPP: Done")

# ============================================================
# CPP: Surgical replacements
# ============================================================
with open(CPP, "r") as f:
    cpp_lines = f.readlines()

# 1. Replace parameter name in declareParameters
for i, line in enumerate(cpp_lines):
    if 'opgsl.altitude.esc' in line:
        cpp_lines[i] = line.replace('opgsl.altitude.esc', 'opgsl.altitude.gp')
        print(f"CPP: Replaced param name at line {i+1}")
    if 'use_esc_altitude_' in line:
        cpp_lines[i] = line.replace('use_esc_altitude_', 'use_gp_altitude_')

# 2. Replace esc_.reset(...) with gp_.reset(...)
for i, line in enumerate(cpp_lines):
    if 'esc_.reset(' in line:
        cpp_lines[i] = line.replace('esc_.reset(', 'gp_.reset(')
        print(f"CPP: Replaced esc_.reset at line {i+1}")

# 3. Replace the ESC residual update BLOCK (lines 383-396 in original)
# Find exact block
esc_block_start = None
esc_block_end = None
for i, line in enumerate(cpp_lines):
    if "// ESC update in TRACK phase" in line:
        esc_block_start = i
    if esc_block_start is not None and "esc_.update(" in line:
        # Find closing ");" 
        esc_block_end = i
        # Check if the closing brace is on next line
        for j in range(i, min(i+5, len(cpp_lines))):
            if cpp_lines[j].strip() == "}":
                esc_block_end = j
                break
        break

if esc_block_start is not None and esc_block_end is not None:
    print(f"CPP: Replacing ESC block lines {esc_block_start+1}-{esc_block_end+1}")
    gp_block = [
        "    // BO+GP: add observation to Gaussian Process\n",
        "    if (alt_phase_ == AltPhase::TRACK && use_gp_altitude_) {\n",
        "        gp_.addObs(current_altitude_, latest_gas_);\n",
        "    }\n",
    ]
    cpp_lines = cpp_lines[:esc_block_start] + gp_block + cpp_lines[esc_block_end+1:]
else:
    print(f"WARN: Could not find ESC block. start={esc_block_start} end={esc_block_end}")

# 4. Replace esc_.getZ() with gp_.getNextZ()
for i, line in enumerate(cpp_lines):
    if 'esc_.getZ()' in line:
        cpp_lines[i] = line.replace('esc_.getZ()', 'gp_.getNextZ()')
        print(f"CPP: Replaced esc_.getZ at line {i+1}")

# 5. Replace ESC log values
for i, line in enumerate(cpp_lines):
    if 'esc_.amplitude, esc_.G_hat,' in line:
        cpp_lines[i] = line.replace('esc_.amplitude, esc_.G_hat,', '0.0f, 0.0f,')
        print(f"CPP: Replaced ESC log values at line {i+1}")
    if 'esc_z={:.2f}' in line:
        cpp_lines[i] = line.replace('esc_z={:.2f}', 'gp_z={:.2f}')
    if 'esc_alt={}' in line:
        cpp_lines[i] = line.replace('esc_alt={}', 'gp_alt={}')

# 6. Check for any remaining esc_ references
cpp_text = "".join(cpp_lines)
remaining = []
idx = 0
while True:
    idx = cpp_text.find("esc_", idx)
    if idx < 0: break
    ctx = cpp_text[max(0,idx-15):idx+20]
    remaining.append((idx, ctx))
    idx += 1
if remaining:
    for pos, ctx in remaining:
        print(f"WARN: remaining esc_ at pos {pos}: ...{ctx}...")
    # Replace any straggler esc_. with gp_.
    cpp_text = cpp_text.replace("esc_.", "gp_.")
    with open(CPP, "w") as f:
        f.write(cpp_text)
else:
    with open(CPP, "w") as f:
        f.writelines(cpp_lines)

print("CPP: Done")

# ============================================================
# Verify
# ============================================================
with open(CPP, "r") as f:
    v = f.read()
with open(HPP, "r") as f:
    vh = f.read()

print("\n=== Verification ===")
checks = [
    (v, "CPP", [("gp_.addObs", "GP addObs"), ("gp_.getNextZ", "GP getNextZ"),
                 ("gp_.reset", "GP reset"), ("use_gp_altitude_", "GP toggle"),
                 ("opgsl.altitude.gp", "GP param")]),
    (vh, "HPP", [("GPState gp_;", "GP struct"), ("struct GPState", "GP struct def"),
                  ("use_gp_altitude_", "GP toggle")])
]
for text, label, items in checks:
    for needle, desc in items:
        print(f"  {label} {'OK' if needle in text else 'MISS'} {desc}")

for remnant in ["esc_.", "ESCState", "use_esc_altitude_"]:
    if remnant in v: print(f"  WARN: '{remnant}' in CPP!")
    if remnant in vh: print(f"  WARN: '{remnant}' in HPP!")

# Brace check
depth = 0
for line in v.split("\n"):
    for c in line:
        if c == "{": depth += 1
        if c == "}": depth -= 1
print(f"\nBrace depth check (CPP): {depth} (should be -1 for namespace)")

print("\nDone!")
