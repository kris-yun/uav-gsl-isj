with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'r') as f:
    content = f.read()

# Add Poisson parameters to SourcePosterior3D class
old_posterior_vars = '''    void reset();
    };
    SourcePosterior3D posterior3d_;'''

new_posterior_vars = '''    // Poisson filament arrival model parameters (shared with OPGSL)
    float poisson_lambda0_ = 2.0f;   // baseline arrival rate (filaments/s)
    float poisson_ell_ = 2.5f;       // characteristic decay length (m)
    float poisson_alpha_w_ = 0.5f;   // wind modulation strength
    float observation_dt_ = 1.0f;    // observation integration time (s)
    float detection_threshold_ = 0.005f;  // binary detection threshold

    void reset();
    };
    SourcePosterior3D posterior3d_;'''

if old_posterior_vars in content:
    content = content.replace(old_posterior_vars, new_posterior_vars)
    print("Added Poisson params to SourcePosterior3D")
else:
    print("WARNING: Could not find SourcePosterior3D vars pattern")

# Add Poisson parameters to OPGSL class (main class level)
old_main_vars = '''    bool use_edpa_=false; bool edpa_should_stop_=false; bool use_event_driven_posterior_=false;
    float detection_threshold_=0.01f;
    float arrival_rate_lambda0_=1.0f,arrival_rate_ell_=2.0f,arrival_rate_alphaw_=0.5f;
    float initial_entropy_=1.0f; bool entropy_initialized_=false;'''

new_main_vars = '''    bool use_edpa_=false; bool edpa_should_stop_=false; bool use_event_driven_posterior_=false;

    // Poisson filament arrival model parameters (calibrated from GADEN)
    float poisson_lambda0_ = 2.0f;   // baseline arrival rate (filaments/s)
    float poisson_ell_ = 2.5f;       // characteristic decay length (m)
    float poisson_alpha_w_ = 0.5f;   // wind modulation strength (dimensionless)
    float observation_dt_ = 1.0f;    // observation integration time (s)
    float detection_threshold_ = 0.005f;  // binary detection threshold (concentration units)
    float initial_entropy_=1.0f; bool entropy_initialized_=false;'''

if old_main_vars in content:
    content = content.replace(old_main_vars, new_main_vars)
    print("Added Poisson params to OPGSL main class")
else:
    print("WARNING: Could not find OPGSL main class vars pattern")

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'w') as f:
    f.write(content)
print("OPGSL.hpp written successfully")