# Strategy: Make the posterior update more robust by:
# 1. Using weaker Poisson parameters (less aggressive non-detection)
# 2. Adding WR-SFE field bias to the posterior (hybrid approach)
# 3. Ensuring the search explores broadly before converging

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    content = f.read()

# Adjust Poisson parameters: even weaker updates
content = content.replace(
    'poisson_lambda0_ = getParam<float>("opgsl.poisson.lambda0", 0.3f);',
    'poisson_lambda0_ = getParam<float>("opgsl.poisson.lambda0", 0.15f);'
)
content = content.replace(
    'poisson_ell_ = getParam<float>("opgsl.poisson.ell", 3.5f);',
    'poisson_ell_ = getParam<float>("opgsl.poisson.ell", 4.0f);'
)
content = content.replace(
    'observation_dt_ = getParam<float>("opgsl.poisson.dt", 0.5f);',
    'observation_dt_ = getParam<float>("opgsl.poisson.dt", 0.3f);'
)

# Increase mixing to 5% to maintain exploration
content = content.replace(
    'float mix_alpha = 0.02f;',
    'float mix_alpha = 0.05f;'
)

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(content)
print("Adjusted: lambda0=0.15, ell=4.0, dt=0.3, mix=5%")