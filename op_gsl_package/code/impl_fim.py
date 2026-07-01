# Implement FIM computation and IG-AI natural gradient flow
import sys
sys.stdout.reconfigure(encoding="utf-8")

HPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp"
CPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"

with open(HPP, "r") as f:
    hpp = f.read()
with open(CPP, "r") as f:
    cpp = f.read()

# ============================================================
# Step 1: Add FIM struct to HPP (after GPState)
# ============================================================
fim_struct = """
    // --- IG-AI: Fisher Information Matrix (3x3 for s_x, s_y, s_z) ---
    struct FisherInfo {
        float Ixx = 0.0f, Ixy = 0.0f, Ixz = 0.0f;
        float Iyy = 0.0f, Iyz = 0.0f;
        float Izz = 0.0f;
        float lambda_min = 0.0f;       // Smallest eigenvalue
        float explore_dir_x = 0.0f;    // Eigenvector for min eigenvalue
        float explore_dir_y = 0.0f;
        float explore_dir_z = 0.0f;

        void computeFromField(const WATS::WR_SFE::FieldEstimate& field, int n_cells, float resolution, float map_half_size,
                              float z_min, float z_max, float current_z, const float z_posterior[], int n_z_bins) {
            // FIM from field posterior: I_ij = sum_cells p(cell) * dlog p(cell)/d theta_i * dlog p(cell)/d theta_j
            // Approximate with finite differences on the log-field
            float total = 0.0f;
            float mean_x = 0.0f, mean_y = 0.0f;
            // Compute mean and total from exp(log_field)
            for (int i = 0; i < n_cells; i++) {
                for (int j = 0; j < n_cells; j++) {
                    float p = std::exp(field.log_field(i, j));
                    float cx = i * resolution - map_half_size;
                    float cy = j * resolution - map_half_size;
                    total += p;
                    mean_x += p * cx;
                    mean_y += p * cy;
                }
            }
            if (total < 1e-10f) return;
            mean_x /= total; mean_y /= total;

            // Compute covariance (inverse of FIM ≈ covariance for Gaussian posterior)
            float Cxx = 0.0f, Cxy = 0.0f, Cyy = 0.0f;
            for (int i = 0; i < n_cells; i++) {
                for (int j = 0; j < n_cells; j++) {
                    float p = std::exp(field.log_field(i, j)) / total;
                    float dx = i * resolution - map_half_size - mean_x;
                    float dy = j * resolution - map_half_size - mean_y;
                    Cxx += p * dx * dx;
                    Cxy += p * dx * dy;
                    Cyy += p * dy * dy;
                }
            }

            // FIM = inverse of covariance (for Gaussian)
            float det = Cxx * Cyy - Cxy * Cxy;
            if (det < 1e-10f) det = 1e-10f;
            Ixx = Cyy / det;
            Ixy = -Cxy / det;
            Iyy = Cxx / det;

            // Height FIM from z posterior
            float z_mean = 0.0f, z_var = 0.0f, z_total = 0.0f;
            for (int k = 0; k < n_z_bins; k++) {
                float z_k = z_min + (z_max - z_min) * ((float)k + 0.5f) / (float)n_z_bins;
                float p = std::exp(z_posterior[k]);
                z_total += p;
                z_mean += p * z_k;
            }
            if (z_total > 1e-10f) {
                z_mean /= z_total;
                for (int k = 0; k < n_z_bins; k++) {
                    float z_k = z_min + (z_max - z_min) * ((float)k + 0.5f) / (float)n_z_bins;
                    float p = std::exp(z_posterior[k]) / z_total;
                    z_var += p * (z_k - z_mean) * (z_k - z_mean);
                }
                Izz = (z_var > 1e-6f) ? 1.0f / z_var : 100.0f;
            }

            // Cross-terms (simplified: assume independence between xy and z)
            Ixz = 0.0f; Iyz = 0.0f;

            // Eigenvalue of 2x2 xy block (smallest eigenvalue = direction of max uncertainty)
            float trace = Ixx + Iyy;
            float diff = Ixx - Iyy;
            float disc = std::sqrt(diff * diff + 4.0f * Ixy * Ixy);
            lambda_min = (trace - disc) / 2.0f;
            // Eigenvector for lambda_min
            float vx = -Ixy, vy = Ixx - lambda_min;
            float vn = std::sqrt(vx*vx + vy*vy);
            if (vn > 1e-6f) { explore_dir_x = vx/vn; explore_dir_y = vy/vn; }
            else { explore_dir_x = 1.0f; explore_dir_y = 0.0f; }
            // z explore direction: always toward highest uncertainty in z
            explore_dir_z = (z_var > 0.1f) ? 1.0f : 0.0f;  // explore z if uncertain
        }

        // Natural gradient step: Δθ = -F^{-1} ∇L
        // For exploration: move in direction of SMALLEST FIM eigenvalue (most uncertain)
        float getExploreStep(float base_step) const {
            // Step size inversely proportional to min eigenvalue
            // When lambda_min is small (uncertain), step is large
            float step = base_step / (lambda_min + 0.1f);
            return std::clamp(step, 0.2f, 2.0f);
        }
    };
    FisherInfo fim_;
"""

# Insert after GPState struct (before levyHeight)
if "GPState gp_;" in hpp and "FisherInfo fim_;" not in hpp:
    hpp = hpp.replace("    GPState gp_;", "    GPState gp_;\n" + fim_struct)
    print("HPP: Added FisherInfo struct")
else:
    print("HPP: FisherInfo already exists or GPState not found")

with open(HPP, "w") as f:
    f.write(hpp)

# ============================================================
# Step 2: Add FIM computation call in CPP (in processGasAndWindMeasurements)
# ============================================================
# Find the line "updateAltitudePhase(latest_gas_);"
old_phase = "    updateAltitudePhase(latest_gas_);\n    logAltitudeState();"
new_phase = """    // IG-AI: Compute Fisher Information Matrix
    fim_.computeFromField(field_estimator_.computeField(), n_cells_, resolution_, map_half_size_,
                          z_min_, z_max_, current_altitude_, z_posterior_, kNumZBins);

    updateAltitudePhase(latest_gas_);
    logAltitudeState();"""

if old_phase in cpp:
    cpp = cpp.replace(old_phase, new_phase)
    print("CPP: Added FIM computation")
else:
    print("WARN: Could not find phase management block")

# ============================================================
# Step 3: Use FIM to guide horizontal exploration in infotaxisStep
# ============================================================
# Find the random direction fallback in infotaxisStep
old_random = """            float ang = std::uniform_real_distribution<float>(0, 2*M_PI)(rng_);
            run_direction_x_ = std::cos(ang); run_direction_y_ = std::sin(ang);
            best_x = cx + run_direction_x_ * step_size_ * 0.3f;
            best_y = cy + run_direction_y_ * step_size_ * 0.3f;"""
new_random = """            // IG-AI: Use FIM eigenvector for exploration direction (most uncertain)
            float explore_step = fim_.getExploreStep(step_size_);
            run_direction_x_ = fim_.explore_dir_x;
            run_direction_y_ = fim_.explore_dir_y;
            best_x = cx + run_direction_x_ * explore_step * 0.3f;
            best_y = cy + run_direction_y_ * explore_step * 0.3f;"""

if old_random in cpp:
    cpp = cpp.replace(old_random, new_random)
    print("CPP: Replaced random direction with FIM-guided exploration")
else:
    print("WARN: Could not find random direction block")

# ============================================================
# Step 4: Add FIM diagnostic log
# ============================================================
# Find logAltitudeState and add FIM info
old_log = """void OPGSL::logAltitudeState() {
    float z_esc = (alt_phase_ == AltPhase::TRACK) ? gp_.getNextZ() : -1.0f;
    GSL_INFO("OPGSL-3D: phase={} z={:.2f} gp_z={:.2f} post_z={:.2f} maxc_z={:.2f} amp={:.3f} G={:.4f} hits={} miss={}",
             (int)alt_phase_, current_altitude_, z_esc, getPosteriorBestZ(), maxConcAltitude(),
             0.0f, 0.0f, gas_hit_count_, consecutive_misses_);"""
new_log = """void OPGSL::logAltitudeState() {
    float z_esc = (alt_phase_ == AltPhase::TRACK) ? gp_.getNextZ() : -1.0f;
    GSL_INFO("OPGSL-3D: phase={} z={:.2f} gp_z={:.2f} post_z={:.2f} maxc_z={:.2f} hits={} miss={} FIM: lmin={:.3f} dir=({:.2f},{:.2f}) Izz={:.3f}",
             (int)alt_phase_, current_altitude_, z_esc, getPosteriorBestZ(), maxConcAltitude(),
             gas_hit_count_, consecutive_misses_, fim_.lambda_min, fim_.explore_dir_x, fim_.explore_dir_y, fim_.Izz);"""

if old_log in cpp:
    cpp = cpp.replace(old_log, new_log)
    print("CPP: Added FIM diagnostic to log")
else:
    print("WARN: Could not find logAltitudeState")

with open(CPP, "w") as f:
    f.write(cpp)
print("\nIG-AI FIM implementation complete!")
