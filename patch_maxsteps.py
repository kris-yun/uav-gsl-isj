# Add max_steps parameter to OPGSL

# 1. Add member variable in header
hpp = open("/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp").read()
if "max_steps_" not in hpp:
    # Find eta_fixed_ member and add max_steps_ after it
    hpp = hpp.replace("float eta_fixed_ = -1.0f;", "float eta_fixed_ = -1.0f;\n    int max_steps_ = -1;")
    open("/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp", "w").write(hpp)
    print("Added max_steps_ to header")
else:
    print("max_steps_ already in header")

# 2. Add parameter reading in cpp
cpp = open("/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp").read()
if "max_steps_" not in cpp:
    # Add after eta_fixed_ parameter reading
    cpp = cpp.replace(
        'posterior3d_.eta_fixed_ = getParam<float>("opgsl.event_driven.eta_fixed", -1.0f);',
        'posterior3d_.eta_fixed_ = getParam<float>("opgsl.event_driven.eta_fixed", -1.0f);\n    max_steps_ = getParam<int>("opgsl.max_steps", -1);'
    )
    # Add max_steps check in checkSourceFound before e-process
    cpp = cpp.replace(
        '    if (use_cp_ && cp_stopping_.shouldStop()) {',
        '    if (max_steps_ > 0 && step_count_ >= max_steps_) {\n        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);\n        GSL_INFO("MAXSTEPS-STOP: step={} MAP=({:.2f},{:.2f},{:.2f})", step_count_, mx, my, mz);\n        convergence_reported_ = true; return GSLResult::Success;\n    }\n    if (use_cp_ && cp_stopping_.shouldStop()) {'
    )
    open("/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp", "w").write(cpp)
    print("Added max_steps_ to cpp")
else:
    print("max_steps_ already in cpp")
