# Recalibrate Poisson parameters
# Problem: alpha_w=0.5 creates wind bias that traps the posterior
# Problem: lambda0=2.0 makes non-detections too informative
# Problem: No posterior mixing allows degeneracy

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    content = f.read()

# Fix 1: Reduce Poisson parameters in declareParameters
content = content.replace(
    'poisson_lambda0_ = getParam<float>("opgsl.poisson.lambda0", 2.0f);',
    'poisson_lambda0_ = getParam<float>("opgsl.poisson.lambda0", 0.3f);'
)
content = content.replace(
    'poisson_ell_ = getParam<float>("opgsl.poisson.ell", 2.5f);',
    'poisson_ell_ = getParam<float>("opgsl.poisson.ell", 3.5f);'
)
content = content.replace(
    'poisson_alpha_w_ = getParam<float>("opgsl.poisson.alpha_w", 0.5f);',
    'poisson_alpha_w_ = getParam<float>("opgsl.poisson.alpha_w", 0.15f);'
)
content = content.replace(
    'observation_dt_ = getParam<float>("opgsl.poisson.dt", 1.0f);',
    'observation_dt_ = getParam<float>("opgsl.poisson.dt", 0.5f);'
)
content = content.replace(
    'detection_threshold_ = getParam<float>("opgsl.poisson.det_threshold", 0.005f);',
    'detection_threshold_ = getParam<float>("opgsl.poisson.det_threshold", 0.001f);'
)

# Fix 2: Add posterior mixing to prevent degeneracy in the update function
old_normalization = '''    // Log-sum-exp normalization (standard for log-domain posteriors)
    float log_sum = -1e9f;
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++) {
                grid[i][j][k] -= max_log;
                log_sum = std::log(std::exp(log_sum) + std::exp(grid[i][j][k]));
            }
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++)
                grid[i][j][k] -= log_sum;'''

new_normalization = '''    // Log-sum-exp normalization with uniform mixing to prevent posterior collapse
    // Mix 2% uniform prior to maintain exploration capability
    float mix_alpha = 0.02f;
    float log_mix = std::log(mix_alpha / (float)(nx_ * ny_ * nz_));
    float log_1_minus_mix = std::log(1.0f - mix_alpha);

    float log_sum = -1e9f;
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++) {
                grid[i][j][k] -= max_log;
                // Mix: (1-alpha)*posterior + alpha*uniform (in log domain)
                grid[i][j][k] = log_1_minus_mix + grid[i][j][k];  // log((1-alpha)*exp(grid))
                // Add uniform component via log-sum-exp
                float mixed = grid[i][j][k];
                if (log_mix > mixed)
                    mixed = log_mix + std::log(1.0f + std::exp(mixed - log_mix));
                else
                    mixed = mixed + std::log(1.0f + std::exp(log_mix - mixed));
                grid[i][j][k] = mixed;
                log_sum = std::log(std::exp(log_sum) + std::exp(grid[i][j][k]));
            }
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++)
                grid[i][j][k] -= log_sum;'''

if old_normalization in content:
    content = content.replace(old_normalization, new_normalization)
    print("Fix 2: Posterior mixing added OK")
else:
    print("WARNING: Normalization block not found for Fix 2")

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(content)

print("Recalibrated parameters:")
print("  lambda0: 2.0 -> 0.3 (milder updates)")
print("  ell: 2.5 -> 3.5 (longer range)")  
print("  alpha_w: 0.5 -> 0.15 (less wind bias)")
print("  dt: 1.0 -> 0.5 (faster integration)")
print("  det_threshold: 0.005 -> 0.001 (more sensitive)")
print("  Added 2% uniform mixing to prevent posterior collapse")