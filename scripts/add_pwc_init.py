# Add PWC initialization to PMFS.cpp
path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp"
with open(path) as f:
    content = f.read()

# Find where to add PWC init - after WRANF mid-nav update block
pwc_init = """
        // PWC: Initialize Plume Wind Correction
        {
            uav_gsl_pwc::Config pcfg;
            pcfg.enabled = getParam<bool>("pwc_enabled", false);
            pcfg.alpha = getParam<double>("pwc_alpha", 50.0);
            pcfg.beta = getParam<double>("pwc_beta", 0.5);
            pcfg.max_correction = getParam<double>("pwc_max_correction", 5.0);
            pcfg.min_wind = getParam<double>("pwc_min_wind", 0.005);
            pcfg.use_adaptive = getParam<bool>("pwc_use_adaptive", true);
            pcfg.plume_scale_factor = getParam<double>("pwc_plume_scale_factor", 1.0);
            pcfg.log_file = getParam<std::string>("pwc_log_file", "/tmp/pwc_log.csv");
            pwcCorrector_.reset(new uav_gsl_pwc::PwcCorrector(pcfg));
            if (pcfg.enabled) {
                GSL_INFO("[PWC] INITIALIZED enabled={} alpha={} beta={} max_corr={}",
                         pcfg.enabled, pcfg.alpha, pcfg.beta, pcfg.max_correction);
            }
        }
"""

if "pwcCorrector_" not in content or "PWC: Initialize" not in content:
    # Insert after the WRANF mid-nav block (before BWE)
    marker = "        // ============================================================\n        // BWE:"
    if marker in content:
        content = content.replace(marker, pwc_init + marker)
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added PWC init to PMFS.cpp")
else:
    print("PWC init already present")
