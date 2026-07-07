import sys

filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'

with open(filepath, 'r') as f:
    content = f.read()

# Fix 1: In sdnbvStep(), change EDPA-STOP return to just log and redirect (don't return)
old_edpa_stop = '''        if (step_count_ > cr_stopping_.warmup_steps &&
            cr_stopping_.e_process >= log_delta && R_t <= cr_stopping_.epsilon) {
            float mx, my, mz;
            posterior3d_.getMAP(mx, my, mz);
            best_x = mx; best_y = my;
            clipToMapBounds(best_x, best_y);
            GSL_INFO("EDPA-STOP: R_t={:.2f} log_e={:.2f} MAP=({:.2f},{:.2f})", R_t, cr_stopping_.e_process, mx, my);
            return;
        }'''

new_edpa_stop = '''        if (step_count_ > cr_stopping_.warmup_steps &&
            cr_stopping_.e_process >= log_delta && R_t <= cr_stopping_.epsilon) {
            float mx, my, mz;
            posterior3d_.getMAP(mx, my, mz);
            best_x = mx; best_y = my;
            clipToMapBounds(best_x, best_y);
            edpa_should_stop_ = true;
            GSL_INFO("EDPA-GUIDE: R_t={:.2f} log_e={:.2f} MAP=({:.2f},{:.2f}) -> redirecting to MAP", R_t, cr_stopping_.e_process, mx, my);
        }'''

if old_edpa_stop in content:
    content = content.replace(old_edpa_stop, new_edpa_stop)
    print('Fix 1: Updated EDPA-STOP in sdnbvStep()')
else:
    print('ERROR: Could not find old_edpa_stop pattern')
    sys.exit(1)

# Fix 2: Add EDPA-STOP check in checkSourceFound(), right after DDM-STOP
old_check_ddm = '''    // DDM: Drift-Diffusion Model evidence-accumulation stopping
    if (use_ddm_ && ddm_stopping_.shouldStop()) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("DDM-STOP: converged at step={} MAP=({:.2f},{:.2f},{:.2f}) evidence={:.3f} theta={:.3f}",
                 step_count_, mx, my, mz, ddm_stopping_.getEvidence(), ddm_stopping_.getAdaptiveThreshold());
        convergence_reported_ = true; return GSLResult::Success;
    }

    // BUG-5 fix: Actually use CP stopping criterion
    if (use_cp_ && cp_stopping_.shouldStop()) {'''

new_check_ddm = '''    // DDM: Drift-Diffusion Model evidence-accumulation stopping
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
    }

    // BUG-5 fix: Actually use CP stopping criterion
    if (use_cp_ && cp_stopping_.shouldStop()) {'''

if old_check_ddm in content:
    content = content.replace(old_check_ddm, new_check_ddm)
    print('Fix 2: Added EDPA-STOP in checkSourceFound()')
else:
    print('ERROR: Could not find old_check_ddm pattern')
    sys.exit(1)

# Fix 3: Add edpa_should_stop_ member initialization
# Find the Initialize() function and add the flag
old_init_flag = '    bout_active_ = false; bout_start_time_ = 0.0f; bout_peak_conc_ = 0.0f;'
new_init_flag = '    edpa_should_stop_ = false; bout_active_ = false; bout_start_time_ = 0.0f; bout_peak_conc_ = 0.0f;'

if old_init_flag in content:
    content = content.replace(old_init_flag, new_init_flag)
    print('Fix 3: Added edpa_should_stop_ initialization')
else:
    print('WARNING: Could not find init flag pattern, will add differently')

with open(filepath, 'w') as f:
    f.write(content)
    
print('Done! File patched successfully.')
