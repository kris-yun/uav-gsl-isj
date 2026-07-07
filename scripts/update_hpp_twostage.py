with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'r') as f:
    content = f.read()

# Add two-stage tracking to SourcePosterior3D
old_reset = '        void reset();'
new_reset = '''        // Two-stage tracking
        bool has_received_detection_ = false;
        float first_detection_x_ = 0.0f;
        float first_detection_y_ = 0.0f;

        void reset();'''
if old_reset in content:
    content = content.replace(old_reset, new_reset)
    print("HPP: Added two-stage tracking to SourcePosterior3D OK")

# Update Poisson defaults
content = content.replace('float poisson_lambda0_ = 0.3f;', 'float poisson_lambda0_ = 0.15f;')
content = content.replace('float poisson_ell_ = 3.5f;', 'float poisson_ell_ = 4.0f;')
content = content.replace('float poisson_alpha_w_ = 0.15f;', 'float poisson_alpha_w_ = 0.15f;')
content = content.replace('float observation_dt_ = 0.5f;', 'float observation_dt_ = 0.3f;')
content = content.replace('float detection_threshold_ = 0.001f;', 'float detection_threshold_ = 0.001f;')
print("HPP: Updated Poisson defaults OK")

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'w') as f:
    f.write(content)