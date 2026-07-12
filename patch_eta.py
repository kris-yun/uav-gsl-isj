import re
content = open("/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp").read()

old_block = """    // Parameter-free eta from surprisal: eta = -log P(observation | MAP)
    // Zero hand-tuned constants. Fully adaptive via Poisson filament model.
    // Theory: surprisal measures how informative the observation is relative
    // to the current best hypothesis (MAP). High surprisal = informative = high eta.
    // This is equivalent to the mutual information I(observation; source | MAP).
    float mx, my, mz; getMAP(mx, my, mz);
    float phi_map = poissonRate(mx, my, cx, cy, wind_x, wind_y, wind_speed);
    phi_map = std::clamp(phi_map, 0.01f, 0.99f);
    float eta;
    if (eta_fixed_ > 0.0f) {
        eta = eta_fixed_;
    } else {
        if (detected) {
            eta = std::clamp(-std::log(phi_map), 0.05f, 1.0f);
        } else {
            eta = std::clamp(-std::log(1.0f - phi_map), 0.05f, 1.0f);
        }
    }"""

new_block = """    // Parameter-free eta from posterior entropy (global measure)
    // Theory: posterior entropy H measures global uncertainty.
    //   H_ratio = H / H_max in [0,1]: 0=concentrated, 1=uniform
    //   eta = H_ratio^1.5 provides natural annealing:
    //     - Early (H_ratio~1): eta~1.0, aggressive exploration
    //     - Late  (H_ratio~0): eta~0.05, conservative refinement
    // Unlike local surprisal (failed), this avoids the negative feedback loop
    // where good MAP -> low phi_map -> low eta -> stops learning.
    // Entropy captures the WHOLE posterior shape, not just the MAP point.
    float H = getEntropy();
    float H_max = std::log((float)(nx_ * ny_ * nz_));
    float H_ratio = std::clamp(H / H_max, 0.0f, 1.0f);
    float eta;
    if (eta_fixed_ > 0.0f) {
        eta = eta_fixed_;
    } else {
        eta = std::clamp(std::pow(H_ratio, 1.5f), 0.05f, 1.0f);
    }
    float mx, my, mz; getMAP(mx, my, mz);"""

if old_block in content:
    content = content.replace(old_block, new_block)
    open("/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp", "w").write(content)
    print("PATCHED: surprisal eta -> entropy eta")
else:
    print("ERROR: old block not found")
    # Show nearby lines
    for i, line in enumerate(content.split('\n')):
        if 'Parameter-free' in line or 'surprisal' in line:
            print(f"  Line {i}: {line}")
