path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path) as f:
    code = f.read()

# ============================================================
# CHANGE 1: Replace plumeLogLikelihood with Active Inference
# generative model using adaptive anisotropic diffusion kernel
# ============================================================

old_plume = """float OPGSL::SourcePosterior3D::plumeLogLikelihood(
    float sx, float sy, float sz,
    float cx, float cy, float cz,
    float wind_x, float wind_y, float wind_speed) const {
    // Gaussian plume model for log-likelihood
    float dx = cx - sx;
    float dy = cy - sy;
    float dz = cz - sz;

    float wind_norm = std::sqrt(wind_x*wind_x + wind_y*wind_y);
    if (wind_norm < 0.01f) {
        // Isotropic diffusion model for near-zero wind
        float dist2 = dx*dx + dy*dy + dz*dz;
        float sigma_iso = 1.5f;  // Large spread for low wind
        return -dist2 / (2*sigma_iso*sigma_iso) - std::log(sigma_iso * 2.507f);
    }

    // Wind-aligned coordinate system
    float wx = wind_x / wind_norm;
    float wy = wind_y / wind_norm;

    // Along-wind distance (from source in wind direction)
    float d_along = dx*wx + dy*wy;
    // Cross-wind distance
    float d_cross = std::abs(dx*wy - dy*wx);
    // Vertical distance
    float dz_abs = std::abs(dz);

    // Plume spreading: sigma increases with downwind distance
    // Using simplified Pasquill-Gifford parameters
    float abs_along = std::abs(d_along);
    float sigma_y = 0.8f * std::sqrt(std::max(d_along, 0.1f) + 0.5f);  // Cross-wind spread
    float sigma_z = 0.5f * std::sqrt(std::max(d_along, 0.1f) + 0.3f);  // Vertical spread

    // Distance attenuation
    float dist = std::sqrt(dx*dx + dy*dy + dz*dz);
    float dist_penalty = -0.4f * dist;  // Attenuate with distance

    // Log-likelihood: Gaussian in cross-wind and vertical
    float log_lik = -d_cross*d_cross/(2*sigma_y*sigma_y)
                    - dz_abs*dz_abs/(2*sigma_z*sigma_z)
                    + dist_penalty;

    // Only for downwind positions (plume doesn't go upwind significantly)
    if (d_along < -1.0f) {
        log_lik -= 3.0f;  // Strong penalty for upwind positions
    }

    return log_lik;
}"""

new_plume = """float OPGSL::SourcePosterior3D::plumeLogLikelihood(
    float sx, float sy, float sz,
    float cx, float cy, float cz,
    float wind_x, float wind_y, float wind_speed) const {
    // ================================================================
    // ACTIVE INFERENCE GENERATIVE MODEL
    // Adaptive Anisotropic Diffusion Kernel
    //
    // Key insight: Gaussian plume assumes steady uniform flow in open
    // space. Indoor environments have recirculation zones, complex
    // geometry, and intermittency. Instead, we use a wind-adaptive
    // kernel that:
    //   - High wind: anisotropic (plume-shaped, aligned with wind)
    //   - Low wind: isotropic (diffusion-dominated spreading)
    //   - No wind: pure distance kernel
    //
    // This replaces the Pasquill-Gifford Gaussian with a kernel that
    // automatically adapts to local flow conditions.
    // ================================================================

    float dx = cx - sx;
    float dy = cy - sy;
    float dz = cz - sz;
    float dist2 = dx*dx + dy*dy + dz*dz;
    float dist = std::sqrt(dist2);

    float wind_norm = std::sqrt(wind_x*wind_x + wind_y*wind_y);

    // ---- Case 1: No wind → isotropic exponential decay ----
    if (wind_norm < 0.05f) {
        // Pure distance-based: p(o|s) ~ exp(-beta * ||o - s||)
        float beta = 0.4f;  // Decay rate
        return -beta * dist - std::log(1.0f + dist);
    }

    // ---- Case 2: Wind present → adaptive anisotropic kernel ----
    float wx = wind_x / wind_norm;
    float wy = wind_y / wind_norm;

    // Decompose distance into wind-aligned components
    float d_parallel = dx*wx + dy*wy;   // Along-wind
    float d_perp_sq = dist2 - d_parallel*d_parallel;  // Cross-wind squared
    float dz_sq = dz*dz;

    // Adaptive sigma: wind speed controls anisotropy
    // u_ref = typical indoor wind (~0.7 m/s for VGR)
    float u_ref = 0.7f;
    float anisotropy = std::min(wind_speed / u_ref, 1.0f);  // 0 to 1

    // High wind (anisotropy ~1): tight along-wind, wider cross-wind
    // Low wind (anisotropy ~0): nearly isotropic
    float sigma_parallel = 2.0f / (anisotropy + 0.15f);  // 2.0 (low) to 0.87 (high)
    float sigma_perp     = 1.2f / (anisotropy + 0.15f);  // 1.2 (low) to 0.52 (high)
    float sigma_z        = 1.0f / (anisotropy + 0.15f);  // 1.0 (low) to 0.43 (high)

    // Log-likelihood: anisotropic Gaussian
    float log_lik = -d_parallel*d_parallel / (2*sigma_parallel*sigma_parallel)
                    -d_perp_sq / (2*sigma_perp*sigma_perp)
                    -dz_sq / (2*sigma_z*sigma_z);

    // Upwind penalty: stronger at high wind, weaker at low wind
    if (d_parallel < -0.5f) {
        log_lik -= 2.0f * anisotropy;  // Only penalize upwind in windy conditions
    }

    // Distance attenuation (plume weakens far from source)
    log_lik -= 0.15f * dist;

    return log_lik;
}"""

if old_plume in code:
    code = code.replace(old_plume, new_plume)
    print("CHANGE 1: Replaced Gaussian plume with Active Inference generative model")
else:
    print("WARNING: Could not find old_plume to replace")

# ============================================================
# CHANGE 2: Add EFE computation to sdnbvStep
# Replace NBV heuristic with Expected Free Energy minimization
# ============================================================

# Find the NBV section in sdnbvStep and replace with EFE
old_nbv_section = """    // NBV: select position that maximizes expected information gain
    float eig_x, eig_y, eig_z;
    posterior3d_.getFIMEigenvalues(eig_x, eig_y, eig_z);

    if (use_sdnbv_ && step_count_ > 15) {
        auto nbv = posterior3d_.selectNBV(cx, cy, current_altitude_, wx, wy, ws);
        if (nbv.expected_info_gain > 0.001f) {
            best_x = nbv.x;
            best_y = nbv.y;
            GSL_INFO("SDNBV-P2: NBV=({:.2f},{:.2f}) EIG={:.4f}", best_x, best_y, nbv.expected_info_gain);
            return;
        }
    }"""

new_efe_section = """    // ================================================================
    // ACTIVE INFERENCE: Expected Free Energy (EFE) Minimization
    //
    // EFE = Epistemic Value + Pragmatic Value
    //
    // Epistemic = information gain about source location
    //   = H[posterior] - E[H[posterior|o]]
    //   → explore regions that reduce uncertainty
    //
    // Pragmatic = expected alignment with goal
    //   = -E[log p(goal|o)]
    //   → exploit regions likely near source
    //
    // The balance is automatic: early on (high entropy), epistemic
    // dominates (explore). As posterior concentrates, pragmatic
    // dominates (converge to source).
    // ================================================================

    if (use_sdnbv_ && step_count_ > 12) {
        float eig_x, eig_y, eig_z;
        posterior3d_.getFIMEigenvalues(eig_x, eig_y, eig_z);

        // Current posterior entropy (for normalization)
        float H_current = posterior3d_.getEntropy();

        // Evaluate EFE at candidate positions
        float best_efe = 1e9f;
        float best_cx = cx, best_cy = cy;

        // Search around robot + MAP midpoint
        float map_x, map_y, map_z;
        posterior3d_.getMAP(map_x, map_y, map_z);
        float center_x = 0.5f * cx + 0.5f * map_x;
        float center_y = 0.5f * cy + 0.5f * map_y;

        float search_r = std::max(2.0f, std::sqrt((map_x-cx)*(map_x-cx)+(map_y-cy)*(map_y-cy))*0.8f + 1.5f);
        float efe_step = 1.0f;

        for (float dx = -search_r; dx <= search_r; dx += efe_step) {
            for (float dy = -search_r; dy <= search_r; dy += efe_step) {
                float cand_x = std::clamp(center_x + dx, x_min_ + 0.5f, x_max_ - 0.5f);
                float cand_y = std::clamp(center_y + dy, y_min_ + 0.5f, y_max_ - 0.5f);

                // Epistemic value: expected information gain
                // Use variance of predicted concentration as proxy
                float mean_c = 0.0f, var_c = 0.0f;
                int n_sample = 0;
                for (int i = 0; i < nx_; i += 2) {
                    for (int j = 0; j < ny_; j += 2) {
                        for (int k = 0; k < nz_; k += 2) {
                            float sx = x_min_ + (i+0.5f) * dx_;
                            float sy = y_min_ + (j+0.5f) * dy_;
                            float sz = z_min_ + (k+0.5f) * dz_;
                            float p = std::exp(grid[i][j][k]);
                            float log_lik = plumeLogLikelihood(sx, sy, sz, cand_x, cand_y,
                                                               current_altitude_, wind_x, wind_y, wind_speed);
                            float c_pred = std::exp(log_lik);
                            mean_c += p * c_pred;
                            var_c += p * c_pred * c_pred;
                            n_sample++;
                        }
                    }
                }
                var_c = var_c - mean_c * mean_c;  // Var = E[X^2] - E[X]^2
                float epistemic = std::sqrt(std::max(var_c, 0.0f));  // Std dev as info gain proxy

                // Pragmatic value: proximity to posterior mass
                // Higher posterior near source → prefer positions close to MAP
                float d_to_map = std::sqrt((cand_x-map_x)*(cand_x-map_x) + (cand_y-map_y)*(cand_y-map_y));
                float pragmatic = std::exp(-0.5f * d_to_map);  // 1 near MAP, 0 far

                // Also consider best-hit proximity
                if (best_hit_conc_ > 0.01f) {
                    float d_to_hit = std::sqrt((cand_x-best_hit_x_)*(cand_x-best_hit_x_) +
                                               (cand_y-best_hit_y_)*(cand_y-best_hit_y_));
                    pragmatic = std::max(pragmatic, std::exp(-0.3f * d_to_hit));
                }

                // EFE = -epistemic + lambda * (1 - pragmatic)
                // Lower EFE = better (more info + closer to goal)
                // lambda increases with steps (shift from explore to exploit)
                float lambda = std::min(2.0f, 0.3f + 0.05f * step_count_);
                float efe = -epistemic + lambda * (1.0f - pragmatic);

                // Distance penalty (prefer closer candidates)
                float d_robot = std::sqrt(dx*dx + dy*dy);
                efe += 0.05f * d_robot;

                if (efe < best_efe) {
                    best_efe = efe;
                    best_cx = cand_x;
                    best_cy = cand_y;
                }
            }
        }

        best_x = best_cx;
        best_y = best_cy;
        GSL_INFO("AI-EFE: ({:.2f},{:.2f}) efe={:.3f} epist={:.3f} H={:.2f} step={}",
                 best_x, best_y, best_efe, H_current, step_count_);
        return;
    }"""

if old_nbv_section in code:
    code = code.replace(old_nbv_section, new_efe_section)
    print("CHANGE 2: Replaced NBV with EFE-based action selection")
else:
    print("WARNING: Could not find old_nbv_section to replace")

# ============================================================
# CHANGE 3: Update log messages to reflect Active Inference
# ============================================================

code = code.replace(
    'GSL_INFO("OPGSL-SDNBV params:',
    'GSL_INFO("OPGSL-ActiveInference params:'
)
code = code.replace(
    'GSL_INFO("OPGSL-SDNBV initialized:',
    'GSL_INFO("OPGSL-ActiveInference initialized:'
)

with open(path, 'w') as f:
    f.write(code)

print("Active Inference framework implemented!")
print("- CHANGE 1: Adaptive anisotropic generative model")
print("- CHANGE 2: EFE-based action selection")
print("- CHANGE 3: Updated naming")