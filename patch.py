#!/usr/bin/env python3
import os
B = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL'

# Fix header
h = open(B+'/OPGSL.hpp').read()
if 'SPRT_Stopping.hpp' not in h:
    h = h.replace('#include "CP_Stopping.hpp"', '#include "CP_Stopping.hpp"\n#include "SPRT_Stopping.hpp"')
if 'sprt_stopping_' not in h:
    h = h.replace('CP::EProcessStopping cp_stopping_;', 'CP::EProcessStopping cp_stopping_;\n    CP::SPRTStopping sprt_stopping_;')
open(B+'/OPGSL.hpp','w').write(h)
print('Header done')

# Fix cpp
c = open(B+'/OPGSL.cpp').read()

# Add SPRT init
if 'sprt_stopping_' not in c:
    init = '\n    CP::SPRTConfig sc; sc.r0_mean=2.0f; sc.r1_mean=0.3f; sc.alpha=0.05f; sc.beta=0.10f;\n    sprt_stopping_ = CP::SPRTStopping(sc);'
    c = c.replace('    cp_stopping_ = CP::EProcessStopping(cp_cfg);', '    cp_stopping_ = CP::EProcessStopping(cp_cfg);'+init)

# Add SPRT addObs
c = c.replace('            cp_stopping_.addObs(residual);', '            cp_stopping_.addObs(residual);\n            sprt_stopping_.addObs(residual);')

# Replace eta
old_e = '''    float eta;
    if (!use_adaptive_eta_) {
        eta = 0.5f;  // Fixed eta for ablation
    } else if (detected) {
        eta = 0.6f + 0.3f * wind_confidence_;  // [0.6, 0.9]
    } else {
        eta = 0.15f + 0.35f * wind_confidence_;  // [0.15, 0.5]
    }'''
new_e = '''    // Kappa-driven adaptive eta with exploration floor (Bissiri et al. 2016)
    float eta;
    if (!use_adaptive_eta_) {
        eta = 0.5f;
    } else {
        float mx, my, mz; getMAP(mx, my, mz);
        float pm = poissonRate(mx, my, cx, cy, wind_x, wind_y, wind_speed);
        pm = std::clamp(pm, 0.01f, 0.99f);
        float kt = std::abs(std::log(pm / (1.0f - pm)));
        kappa_step_count_++;
        float aa = kappa_step_count_ <= 10 ? 1.0f/kappa_step_count_ : kappa_ema_alpha_;
        float d = kt - kappa_ema_mean_;
        kappa_ema_mean_ += aa * d;
        kappa_ema_var_ = (1.0f-aa)*(kappa_ema_var_ + aa*d*d);
        float ks = std::sqrt(std::max(kappa_ema_var_, 0.01f));
        float z = (kt - kappa_ema_mean_) / ks;
        float ke = std::clamp(1.0f/(1.0f+std::exp(-z)), 0.05f, 0.95f);
        float ef = std::max(0.4f*std::exp(-kappa_step_count_/40.0f), 0.05f);
        eta = std::clamp(std::max(ke, ef), 0.05f, 0.95f);
    }'''
if old_e in c:
    c = c.replace(old_e, new_e)
    print('Eta replaced')
else:
    print('WARNING: eta block not found')

# Replace checkSourceFound
si = c.find('GSLResult OPGSL::checkSourceFound()')
if si >= 0:
    d = 0; ei = si
    for i in range(si, len(c)):
        if c[i]=='{': d+=1
        elif c[i]=='}':
            d-=1
            if d==0: ei=i+1; break
    nc = '''GSLResult OPGSL::checkSourceFound() {
    // Dual-path: E-process + SPRT (Wald 1945) + timeout
    if (convergence_reported_) return GSLResult::Success;
    if (elapsed_time_ < 10.0f) return GSLResult::Running;
    if (gas_hit_count_ < 3) return GSLResult::Running;
    if (step_count_ < 8) return GSLResult::Running;
    if (use_cp_ && cp_stopping_.shouldStop()) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("EP-STOP: step={} MAP=({:.2f},{:.2f},{:.2f})", step_count_, mx, my, mz);
        convergence_reported_ = true; return GSLResult::Success;
    }
    int sprt = sprt_stopping_.checkStopping();
    if (sprt == 1) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("SPRT-STOP: step={} MAP=({:.2f},{:.2f},{:.2f}) LLR={:.3f}", step_count_, mx, my, mz, sprt_stopping_.getCumulativeLLR());
        convergence_reported_ = true; return GSLResult::Success;
    }
    if (elapsed_time_ > 235.0f) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("TIMEOUT: MAP=({:.2f},{:.2f},{:.2f}) step={}", mx, my, mz, step_count_);
        convergence_reported_ = true; return GSLResult::Success;
    }
    if (step_count_ >= 300) return GSLResult::Failure;
    return GSLResult::Running;
}'''
    c = c[:si] + nc + c[ei:]
    print('Convergence replaced')
else:
    print('WARNING: checkSourceFound not found')

open(B+'/OPGSL.cpp','w').write(c)
print('All done!')
