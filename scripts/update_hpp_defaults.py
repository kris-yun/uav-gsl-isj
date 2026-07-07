with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'r') as f:
    content = f.read()

# Update SourcePosterior3D default params
content = content.replace('float poisson_lambda0_ = 2.0f;', 'float poisson_lambda0_ = 0.3f;')
content = content.replace('float poisson_ell_ = 2.5f;', 'float poisson_ell_ = 3.5f;')
content = content.replace('float poisson_alpha_w_ = 0.5f;', 'float poisson_alpha_w_ = 0.15f;')
content = content.replace('float observation_dt_ = 1.0f;', 'float observation_dt_ = 0.5f;')
content = content.replace('float detection_threshold_ = 0.005f;', 'float detection_threshold_ = 0.001f;')

# Update OPGSL class defaults too
content = content.replace('float poisson_lambda0_ = 2.0f;', 'float poisson_lambda0_ = 0.3f;')
content = content.replace('float poisson_ell_ = 2.5f;', 'float poisson_ell_ = 3.5f;')

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'w') as f:
    f.write(content)
print("HPP defaults updated")