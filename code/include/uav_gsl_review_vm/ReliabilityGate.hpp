#pragma once

#include "uav_gsl_review/DirectionalDeconvRefiner.hpp"
#include "uav_gsl_review/EvidenceGate.hpp"
#include "uav_gsl_review/GridTypes.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

namespace uav_gsl_review {

struct CandidateEstimate {
    std::string name;
    Vec2 xy{0.0, 0.0};
    bool valid{false};
    double internal_score{0.0};
};

struct ReliabilityGateConfig {
    int dirl_min_hits{5};
    double dirl_min_wind_coherence{0.25};
    double dirl_min_peak_mass_ratio{0.005};
    double max_dirl_pmfs_disagreement_m{6.0};

    // If evidence is weak and DIRL moves far away from PMFS/centroid, reject it.
    double weak_evidence_max_correction_m{2.0};

    // Blend DIRL with PMFS rather than hard replacing it when reliability is moderate.
    bool allow_blend{true};
    double min_blend_weight{0.20};
    double max_blend_weight{0.85};
};

struct ReliabilityDecision {
    CandidateEstimate selected;
    Vec2 fused_xy{0.0, 0.0};
    double dirl_reliability{0.0};
    double blend_weight{0.0};
    std::string reason;
};

class ReliabilityGate {
public:
    explicit ReliabilityGate(ReliabilityGateConfig cfg = {}) : cfg_(cfg) {}

    ReliabilityDecision select(const EvidenceSummary& evidence,
                               const CandidateEstimate& pmfs,
                               const CandidateEstimate& peak_gas,
                               const CandidateEstimate& hit_centroid,
                               const DirectionalDeconvResult& dirl) const {
        ReliabilityDecision out;
        out.selected = pmfs;
        out.fused_xy = pmfs.xy;

        if (!pmfs.valid) {
            out.reason = "pmfs_invalid";
            return out;
        }

        CandidateEstimate dirl_cand;
        dirl_cand.name = "dirl_allhits";
        dirl_cand.xy = dirl.peak_estimate;
        dirl_cand.valid = dirl.valid;
        dirl_cand.internal_score = dirl.peak_mass_ratio;

        if (!dirl.valid) {
            out.reason = std::string("dirl_invalid:") + dirl.reason;
            // If PMFS is weak but peak/centroid exists, use transparent fallback only if asked in ablation.
            return maybeFallback(evidence, pmfs, peak_gas, hit_centroid, out);
        }

        const double d_pmfs = distance(pmfs.xy, dirl.peak_estimate);
        const bool enough_hits = evidence.hit_count >= cfg_.dirl_min_hits;
        const bool wind_ok = evidence.wind_coherence >= cfg_.dirl_min_wind_coherence;
        const bool peak_ok = dirl.peak_mass_ratio >= cfg_.dirl_min_peak_mass_ratio;
        const bool disagreement_ok = d_pmfs <= cfg_.max_dirl_pmfs_disagreement_m;

        const double hit_score = clamp01((evidence.hit_count - cfg_.dirl_min_hits + 1) / 10.0);
        const double wind_score = clamp01((evidence.wind_coherence - cfg_.dirl_min_wind_coherence) /
                                          std::max(1e-9, 1.0 - cfg_.dirl_min_wind_coherence));
        const double peak_score = clamp01(dirl.peak_mass_ratio / std::max(1e-9, cfg_.dirl_min_peak_mass_ratio * 4.0));
        const double entropy_score = clamp01(1.0 - dirl.entropy_norm);

        out.dirl_reliability = 0.30 * hit_score + 0.25 * wind_score + 0.25 * peak_score + 0.20 * entropy_score;

        std::ostringstream why;
        why << "dirl_rel=" << out.dirl_reliability
            << "|d_pmfs=" << d_pmfs
            << "|hits=" << evidence.hit_count
            << "|windC=" << evidence.wind_coherence
            << "|dirlPeak=" << dirl.peak_mass_ratio;

        if (!enough_hits) why << "|reject_low_hits";
        if (!wind_ok) why << "|reject_low_wind";
        if (!peak_ok) why << "|reject_low_peak";
        if (!disagreement_ok) why << "|reject_large_disagreement";

        const bool weak_evidence = !enough_hits || !wind_ok || evidence.hit_bbox_diag_m < 0.75;
        if (weak_evidence && d_pmfs > cfg_.weak_evidence_max_correction_m) {
            why << "|reject_weak_evidence_large_move";
            out.reason = why.str();
            return maybeFallback(evidence, pmfs, peak_gas, hit_centroid, out);
        }

        if (enough_hits && wind_ok && peak_ok && disagreement_ok) {
            if (cfg_.allow_blend && out.dirl_reliability < 0.80) {
                const double w = cfg_.min_blend_weight +
                                 (cfg_.max_blend_weight - cfg_.min_blend_weight) *
                                 clamp01((out.dirl_reliability - 0.35) / 0.45);
                out.selected = CandidateEstimate{"pmfs_dirl_blend", pmfs.xy, true, out.dirl_reliability};
                out.blend_weight = w;
                out.fused_xy = Vec2{(1.0 - w) * pmfs.xy.x + w * dirl.peak_estimate.x,
                                    (1.0 - w) * pmfs.xy.y + w * dirl.peak_estimate.y};
                why << "|blend_w=" << w;
            } else {
                out.selected = dirl_cand;
                out.fused_xy = dirl.peak_estimate;
                out.blend_weight = 1.0;
                why << "|select_dirl";
            }
        } else {
            out = maybeFallback(evidence, pmfs, peak_gas, hit_centroid, out);
            why << "|select_" << out.selected.name;
        }

        out.reason = why.str();
        return out;
    }

private:
    ReliabilityGateConfig cfg_;

    static double clamp01(double v) {
        return std::max(0.0, std::min(1.0, v));
    }

    ReliabilityDecision maybeFallback(const EvidenceSummary& evidence,
                                      const CandidateEstimate& pmfs,
                                      const CandidateEstimate& peak_gas,
                                      const CandidateEstimate& hit_centroid,
                                      ReliabilityDecision current) const {
        // Default remains PMFS. Peak/centroid fallback is deliberately conservative and should
        // be ablated separately; otherwise reviewers will say the method is secretly peak-gas.
        current.selected = pmfs;
        current.fused_xy = pmfs.xy;
        current.blend_weight = 0.0;

        const bool pmfs_very_uncertain = evidence.posterior_entropy_norm > 0.97 &&
                                         evidence.posterior_peak_ratio < 0.01;
        if (pmfs_very_uncertain && hit_centroid.valid && evidence.hit_count >= cfg_.dirl_min_hits) {
            current.selected = hit_centroid;
            current.fused_xy = hit_centroid.xy;
            current.reason += "|fallback_hit_centroid";
        } else if (pmfs_very_uncertain && peak_gas.valid && evidence.hit_count >= cfg_.dirl_min_hits) {
            current.selected = peak_gas;
            current.fused_xy = peak_gas.xy;
            current.reason += "|fallback_peak_gas";
        } else {
            current.reason += "|fallback_pmfs";
        }
        return current;
    }
};

} // namespace uav_gsl_review
