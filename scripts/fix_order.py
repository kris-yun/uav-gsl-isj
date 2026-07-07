filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    content = f.read()

# Find the block from checkSourceFound and reorder: EDPA first, then CP, then DDM
old_block = '''    // BUG-5 fix: Actually use CP stopping criterion
    if (use_cp_ && cp_stopping_.shouldStop()) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("CP-STOP: converged at step={} MAP=({:.2f},{:.2f},{:.2f}) width={:.3f}",
                 step_count_, mx, my, mz, cp_stopping_.getWidth());
        convergence_reported_ = true; return GSLResult::Success;
    }

    // DDM: Drift-Diffusion Model evidence-accumulation stopping
    if (use_ddm_ && ddm_stopping_.shouldStop()) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("DDM-STOP: converged at step={} MAP=({:.2f},{:.2f},{:.2f}) evidence={:.3f} theta={:.3f}",
                 step_count_, mx, my, mz, ddm_stopping_.getEvidence(), ddm_stopping_.getAdaptiveThreshold());
        convergence_reported_ = true; return GSLResult::Success;
    }

    // EDPA: Anytime-valid stopping via credible region contraction
    if (use_edpa_ && edpa_should_stop_) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        float R_t = computeCredibleRegionRadius();
        GSL_INFO("EDPA-STOP: converged at step={} MAP=({:.2f},{:.2f}) R_t={:.2f} log_e={:.1f}",
                 step_count_, mx, my, R_t, cr_stopping_.e_process);
        convergence_reported_ = true; return GSLResult::Success;
    }'''

new_block = '''    // EDPA: Anytime-valid stopping via credible region contraction (highest priority)
    if (use_edpa_ && edpa_should_stop_) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        float R_t = computeCredibleRegionRadius();
        GSL_INFO("EDPA-STOP: converged at step={} MAP=({:.2f},{:.2f}) R_t={:.2f} log_e={:.1f}",
                 step_count_, mx, my, R_t, cr_stopping_.e_process);
        convergence_reported_ = true; return GSLResult::Success;
    }

    // CP: Conformal Prediction stopping criterion
    if (use_cp_ && cp_stopping_.shouldStop()) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("CP-STOP: converged at step={} MAP=({:.2f},{:.2f},{:.2f}) width={:.3f}",
                 step_count_, mx, my, mz, cp_stopping_.getWidth());
        convergence_reported_ = true; return GSLResult::Success;
    }

    // DDM: Drift-Diffusion Model evidence-accumulation stopping
    if (use_ddm_ && ddm_stopping_.shouldStop()) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("DDM-STOP: converged at step={} MAP=({:.2f},{:.2f},{:.2f}) evidence={:.3f} theta={:.3f}",
                 step_count_, mx, my, mz, ddm_stopping_.getEvidence(), ddm_stopping_.getAdaptiveThreshold());
        convergence_reported_ = true; return GSLResult::Success;
    }'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(filepath, 'w') as f:
        f.write(content)
    print('Reordered: EDPA-STOP now has highest priority')
else:
    print('ERROR: pattern not found')
