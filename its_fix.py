import re

f = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS_utils.cpp"
with open(f, "r") as fh:
    code = fh.read()

old = """                // ITS: Inertia Tensor Selection. From astronomical image analysis.
                // Computes eccentricity of hit distribution to adaptively control SDR.
                // Circular hits (near source) -> skip SDR. Elongated (far source) -> use SDR.
                if (raw_hce_hit_count >= 5) {
                    double cx = 0.0, cy = 0.0;
                    for (auto& p : raw_hit_positions_) { cx += p.first; cy += p.second; }
                    int n = raw_hit_positions_.size();
                    cx /= n; cy /= n;
                    double mxx = 0.0, myy = 0.0, mxy = 0.0;
                    for (auto& p : raw_hit_positions_) {
                        double dx = p.first - cx, dy = p.second - cy;
                        mxx += dx * dx;
                        myy += dy * dy;
                        mxy += dx * dy;
                    }
                    mxx /= n; myy /= n; mxy /= n;
                    double trace = mxx + myy;
                    double det = mxx * myy - mxy * mxy;
                    double disc = std::sqrt(std::max(0.0, trace * trace / 4.0 - det));
                    double lambda1 = trace / 2.0 + disc;
                    double lambda2 = trace / 2.0 - disc;
                    double ecc = (lambda1 > 1e-10) ? std::sqrt(1.0 - lambda2 / lambda1) : 0.0;
                    const double ecc_threshold = 0.7;
                    // Continuous blend: w=ecc interpolates between baseline and SDR.
                    // ecc~0 (circular) -> keep baseline; ecc~1 (elongated) -> use SDR.
                    double total_var = mxx + myy;
                    double var_norm = std::min(1.0, total_var / 9.0);
                    double w = ecc * var_norm;
                    sourceLocation.x = (1.0 - w) * sourceLocation.x + w * sdrEst.x;
                    sourceLocation.y = (1.0 - w) * sourceLocation.y + w * sdrEst.y;
                    selectedEstimator = "its_blend";
                    GSL_INFO("[ITS] blend: ecc={:.3f} var={:.3f} varN={:.3f} w={:.3f} est=({:.2f},{:.2f})", ecc, total_var, var_norm, w, sourceLocation.x, sourceLocation.y);
                }"""

new = """                // ITS-G: Inertia Tensor Gating (from astronomical image analysis).
                // Gate SDR application: elongated hit distribution -> apply SDR directly.
                if (raw_hce_hit_count >= 5) {
                    double cx = 0.0, cy = 0.0;
                    for (auto& p : raw_hit_positions_) { cx += p.first; cy += p.second; }
                    int n = raw_hit_positions_.size();
                    cx /= n; cy /= n;
                    double mxx = 0.0, myy = 0.0, mxy = 0.0;
                    for (auto& p : raw_hit_positions_) {
                        double dx = p.first - cx, dy = p.second - cy;
                        mxx += dx * dx;
                        myy += dy * dy;
                        mxy += dx * dy;
                    }
                    mxx /= n; myy /= n; mxy /= n;
                    double trace = mxx + myy;
                    double det = mxx * myy - mxy * mxy;
                    double disc = std::sqrt(std::max(0.0, trace * trace / 4.0 - det));
                    double lambda1 = trace / 2.0 + disc;
                    double lambda2 = trace / 2.0 - disc;
                    double ecc = (lambda1 > 1e-10) ? std::sqrt(1.0 - lambda2 / lambda1) : 0.0;
                    const double ecc_threshold = 0.3;
                    // Hard gate: elongated hits -> use SDR directly, no blend dilution.
                    if (ecc >= ecc_threshold) {
                        sourceLocation.x = sdrEst.x;
                        sourceLocation.y = sdrEst.y;
                        selectedEstimator = "its_sdr";
                        GSL_INFO("[ITS-G] ecc={:.3f} >= {:.3f} -> SDR direct, est=({:.2f},{:.2f})", ecc, ecc_threshold, sdrEst.x, sdrEst.y);
                    } else {
                        GSL_INFO("[ITS-G] ecc={:.3f} < {:.3f} -> keeping baseline", ecc, ecc_threshold);
                    }
                } else {
                    sourceLocation.x = sdrEst.x;
                    sourceLocation.y = sdrEst.y;
                    selectedEstimator = "sdr_direct";
                    GSL_INFO("[SDR-direct] est=({:.2f},{:.2f})", sdrEst.x, sdrEst.y);
                }"""

if old in code:
    code = code.replace(old, new)
    with open(f, "w") as fh:
        fh.write(code)
    print("PATCHED_OK")
else:
    print("OLD_BLOCK_NOT_FOUND")
    # Debug: find the line
    for i, line in enumerate(code.split("\n"), 1):
        if "ITS:" in line or "Inertia Tensor" in line:
            print(f"  Line {i}: {line.strip()}")
