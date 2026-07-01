path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path) as f:
    lines = f.readlines()
code = "".join(lines)

# === CHANGE 1: Replace plumeLogLikelihood (lines 162-195) ===
old_plume = '''float OPGSL::SourcePosterior3D::plumeLogLikelihood(float sx, float sy, float sz,
                                                     float cx, float cy, float cz,
                                                     float wind_x, float wind_y, float wind_speed) const {
    float dx = cx - sx, dy = cy - sy, dz = cz - sz;
    float dist2 = dx*dx + dy*dy + dz*dz;
    float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y);

    if (wn < 0.08f) {
        // ISOTROPIC DIFFUSION MODEL for indoor/low-wind scenarios
        float sigma = 0.6f;
        float log_lik = -dist2 / (sigma * sigma) - 0.3f * std::sqrt(dist2);
        if (dz < -0.5f) log_lik -= 0.5f * (dz + 0.5f) * (dz + 0.5f);
        return log_lik;
    } else {
        // Wind-advected Gaussian plume
        float wx = wind_x/wn, wy = wind_y/wn;
        float d_along = dx*wx + dy*wy;
        float d_cross = std::abs(dx*wy - dy*wx);
        float d_vert = std::abs(dz);
        float sigma_y = 0.8f * std::sqrt(std::max(d_along, 0.1f) + 0.5f);
        float sigma_z = 0.5f * std::sqrt(std::max(d_along, 0.1f) + 0.5f);
        float log_lik = -d_cross*d_cross/(2*sigma_y*sigma_y) - d_vert*d_vert/(2*sigma_z*sigma_z);
        if (d_along < 0) log_lik -= 2.0f * std::abs(d_along);
        float dist_xy = std::sqrt(dx*dx + dy*dy);
        log_lik -= 0.4f * dist_xy;
        return log_lik;
    }
}'''

new_plume = '''float OPGSL::SourcePosterior3D::plumeLogLikelihood(float sx, float sy, float sz,
                                                     float cx, float cy, float cz,
                                                     float wind_x, float wind_y, float wind_speed) const {
    // ================================================================
    // ACTIVE INFERENCE GENERATIVE MODEL: Adaptive Anisotropic Kernel
    //
    // Replaces Gaussian plume (assumes steady uniform open-space flow)
    // with a wind-adaptive kernel for indoor environments:
    //   High wind -> anisotropic (aligned with wind, tight)
    //   Low wind  -> isotropic (diffusion-dominated, broad)
    //   No wind   -> pure distance decay
    //
    // Physical basis: In indoor environments, the key issue is NOT
    // low Peclet number (Pe~10^5 for VGR), but rather complex geometry
    // causing recirculation zones, intermittency, and non-Gaussian
    // concentration distributions. This kernel captures the essential
    // monotonic relationship (closer to source -> higher expected
    // concentration) without assuming a specific plume shape.
    // ================================================================

    float dx = cx - sx, dy = cy - sy, dz = cz - sz;
    float dist2 = dx*dx + dy*dy + dz*dz;
    float dist = std::sqrt(dist2);
    float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y);

    // ---- No wind: isotropic exponential decay ----
    if (wn < 0.05f) {
        float beta = 0.4f;
        return -beta * dist - 0.15f * dist2;
    }

    // ---- Wind present: adaptive anisotropic kernel ----
    float wx = wind_x / wn, wy = wind_y / wn;
    float d_parallel = dx*wx + dy*wy;       // Along-wind component
    float d_perp_sq = dist2 - d_parallel*d_parallel;  // Cross-wind squared
    float dz_sq = dz*dz;

    // Anisotropy adapts to wind speed
    float u_ref = 0.7f;
    float anisotropy = std::min(wn / u_ref, 1.0f);

    // Adaptive spreading: low wind -> large sigma (isotropic), high wind -> small (anisotropic)
    float sig_par = 2.0f / (anisotropy + 0.15f);
    float sig_perp = 1.2f / (anisotropy + 0.15f);
    float sig_z = 1.0f / (anisotropy + 0.15f);

    float log_lik = -d_parallel*d_parallel / (2*sig_par*sig_par)
                    -d_perp_sq / (2*sig_perp*sig_perp)
                    -dz_sq / (2*sig_z*sig_z);

    // Upwind penalty (weaker in low wind)
    if (d_parallel < -0.5f)
        log_lik -= 2.0f * anisotropy * std::abs(d_parallel);

    // Distance attenuation
    log_lik -= 0.15f * dist;

    return log_lik;
}'''

if old_plume in code:
    code = code.replace(old_plume, new_plume)
    print("OK: plumeLogLikelihood replaced with Active Inference kernel")
else:
    print("FAIL: could not match plumeLogLikelihood")

# === CHANGE 2: Replace NBV with EFE (lines 508-520) ===
old_nbv = '''    // NBV: select position with highest expected info gain
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
    }'''

new_efe = '''    // ================================================================
    // ACTIVE INFERENCE: Expected Free Energy (EFE) Minimization
    //
    // EFE = Epistemic Value + lambda * Pragmatic Value
    //   Epistemic  = predicted information gain (explore uncertainty)
    //   Pragmatic  = proximity to posterior mass (exploit belief)
    //   lambda     = increases with steps (explore -> exploit shift)
    //
    // This naturally balances exploration and exploitation under one
    // principled objective, replacing ad-hoc NBV heuristics.
    // ================================================================

    if (use_sdnbv_ && step_count_ > 12) {
        float eig_x, eig_y, eig_z;
        posterior3d_.getFIMEigenvalues(eig_x, eig_y, eig_z);
        float H_current = posterior3d_.getEntropy();

        float map_x, map_y, map_z;
        posterior3d_.getMAP(map_x, map_y, map_z);
        float center_x = 0.5f * cx + 0.5f * map_x;
        float center_y = 0.5f * cy + 0.5f * map_y;
        float dist_to_map = std::sqrt((map_x-cx)*(map_x-cx) + (map_y-cy)*(map_y-cy));
        float search_r = std::max(2.0f, dist_to_map * 0.8f + 1.5f);
        float efe_step = 1.0f;

        float best_efe = 1e9f;
        float best_cx = cx, best_cy = cy;

        for (float fdx = -search_r; fdx <= search_r; fdx += efe_step) {
            for (float fdy = -search_r; fdy <= search_r; fdy += efe_step) {
                float cand_x = std::clamp(center_x + fdx, x_min_ + 0.5f, x_max_ - 0.5f);
                float cand_y = std::clamp(center_y + fdy, y_min_ + 0.5f, y_max_ - 0.5f);

                // Epistemic: predicted concentration variance
                float mean_c = 0.0f, var_c = 0.0f;
                for (int ii = 0; ii < nx_; ii += 2) {
                    for (int jj = 0; jj < ny_; jj += 2) {
                        for (int kk = 0; kk < nz_; kk += 2) {
                            float psx = x_min_ + (ii+0.5f) * dx_;
                            float psy = y_min_ + (jj+0.5f) * dy_;
                            float psz = z_min_ + (kk+0.5f) * dz_;
                            float p = std::exp(grid[ii][jj][kk]);
                            float ll = plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,
                                                          current_altitude_, wind_x, wind_y, wind_speed);
                            float cp = std::exp(ll);
                            mean_c += p * cp;
                            var_c += p * cp * cp;
                        }
                    }
                }
                var_c = var_c - mean_c * mean_c;
                float epistemic = std::sqrt(std::max(var_c, 0.0f));

                // Pragmatic: proximity to posterior mass + best hit
                float d_map = std::sqrt((cand_x-map_x)*(cand_x-map_x) + (cand_y-map_y)*(cand_y-map_y));
                float pragmatic = std::exp(-0.5f * d_map);
                if (best_hit_conc_ > 0.01f) {
                    float d_hit = std::sqrt((cand_x-best_hit_x_)*(cand_x-best_hit_x_) +
                                            (cand_y-best_hit_y_)*(cand_y-best_hit_y_));
                    pragmatic = std::max(pragmatic, std::exp(-0.3f * d_hit));
                }

                // EFE: balance explore/exploit
                float lambda = std::min(2.0f, 0.3f + 0.05f * step_count_);
                float efe = -epistemic + lambda * (1.0f - pragmatic) + 0.05f * std::sqrt(fdx*fdx + fdy*fdy);

                if (efe < best_efe) {
                    best_efe = efe;
                    best_cx = cand_x;
                    best_cy = cand_y;
                }
            }
        }

        best_x = best_cx;
        best_y = best_cy;
        GSL_INFO("AI-EFE: ({:.2f},{:.2f}) efe={:.3f} H={:.2f} step={}", best_x, best_y, best_efe, H_current, step_count_);
        return;
    }'''

if old_nbv in code:
    code = code.replace(old_nbv, new_efe)
    print("OK: NBV replaced with EFE action selection")
else:
    print("FAIL: could not match NBV section")

# === CHANGE 3: Rename log messages ===
code = code.replace('GSL_INFO("OPGSL-SDNBV params:', 'GSL_INFO("OPGSL-ActiveInference params:')
code = code.replace('GSL_INFO("OPGSL-SDNBV initialized:', 'GSL_INFO("OPGSL-ActiveInference initialized:')
code = code.replace('GSL_INFO("OPGSL-SDNBV step=', 'GSL_INFO("OPGSL-AI step=')

with open(path, 'w') as f:
    f.write(code)
print("All Active Inference changes written!")