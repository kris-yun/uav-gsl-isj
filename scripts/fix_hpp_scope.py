with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'r') as f:
    content = f.read()

# Add Poisson params to SourcePosterior3D (before reset)
old = '''        // Two-stage tracking
        bool has_received_detection_ = false;
        float first_detection_x_ = 0.0f;
        float first_detection_y_ = 0.0f;

        void reset();'''

new = '''        // Poisson model parameters
        float poisson_lambda0_ = 0.15f;
        float poisson_ell_ = 4.0f;
        float poisson_alpha_w_ = 0.15f;
        float observation_dt_ = 0.3f;
        float detection_threshold_ = 0.001f;

        // Two-stage tracking
        bool has_received_detection_ = false;
        float first_detection_x_ = 0.0f;
        float first_detection_y_ = 0.0f;

        void reset();'''

if old in content:
    content = content.replace(old, new)
    print("Added Poisson params to SourcePosterior3D")
else:
    print("ERROR: pattern not found")

# Also update OPGSL class defaults
content = content.replace('float poisson_lambda0_ = 2.0f;', 'float poisson_lambda0_ = 0.15f;')
content = content.replace('float poisson_ell_ = 2.5f;', 'float poisson_ell_ = 4.0f;')
content = content.replace('float poisson_alpha_w_ = 0.5f;', 'float poisson_alpha_w_ = 0.15f;')

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'w') as f:
    f.write(content)
print("HPP updated")