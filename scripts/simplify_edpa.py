#!/usr/bin/env python3
"""Simplify EDPA to Layer 3 stopping only"""
path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path, "r") as f:
    c = f.read()

# Find the EDPA mode block and replace it
marker = "    // ====== EDPA-GSL Mode"
if marker not in c:
    # Try the new marker
    marker = "    // ====== EDPA-GSL Mode: Layer 3"
    
start = c.find(marker)
if start < 0:
    print("Could not find EDPA block")
    exit(1)

# Find the end of the EDPA block (the return; followed by })
# Search for the closing of the if(use_edpa_) block
depth = 0
i = start
end = -1
while i < len(c):
    if c[i] == '{':
        depth += 1
    elif c[i] == '}':
        depth -= 1
        if depth == 0:
            end = i + 1
            break
    i += 1

if end < 0:
    print("Could not find end of EDPA block")
    exit(1)

new_block = """    // ====== EDPA-GSL Mode: Layer 3 Stopping ======
    if (use_edpa_) {
        // Layer 3: Compute credible region and check stopping
        float R_t = computeCredibleRegionRadius();
        float log_delta = std::log(1.0f / cr_stopping_.delta);
        float contraction = cr_stopping_.prev_radius - R_t;
        if (contraction > 0) cr_stopping_.e_process += std::log1p(cr_stopping_.eta * contraction);
        cr_stopping_.prev_radius = R_t;
        
        if (step_count_ > cr_stopping_.warmup_steps &&
            cr_stopping_.e_process >= log_delta && R_t <= cr_stopping_.epsilon) {
            float mx, my, mz;
            posterior3d_.getMAP(mx, my, mz);
            best_x = mx; best_y = my;
            clipToMapBounds(best_x, best_y);
            GSL_INFO("EDPA-STOP: R_t={:.2f} log_e={:.2f} MAP=({:.2f},{:.2f})", R_t, cr_stopping_.e_process, mx, my);
            return;
        }
        
        // Layer 2: Compute gamma for monitoring
        float H_t = posterior3d_.getEntropy();
        if (!entropy_initialized_) { initial_entropy_ = H_t; entropy_initialized_ = true; }
        float gamma = (initial_entropy_ > 1e-6f) ? (H_t / initial_entropy_) : 0.0f;
        gamma = std::clamp(gamma, 0.0f, 1.0f);
        
        // Log EDPA status, then fall through to original search
        GSL_INFO("EDPA-STATUS: g={:.2f} R={:.2f} log_e={:.1f} s={}", gamma, R_t, cr_stopping_.e_process, step_count_);
    }
"""

c = c[:start] + new_block + c[end:]
with open(path, "w") as f:
    f.write(c)
print("EDPA simplified to Layer 3 stopping only")
