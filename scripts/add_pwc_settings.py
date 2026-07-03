# Add PWC settings to Settings.hpp
path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/internal/Settings.hpp"
with open(path) as f:
    content = f.read()

pwc_settings = """
        // PWC: Plume Wind Correction
        struct PwcSettings {
            bool enabled{false};
            double alpha{50.0};
            double beta{0.5};
            double max_correction{5.0};
            double min_wind{0.005};
            bool use_adaptive{true};
            double plume_scale_factor{1.0};
        } pwc;
"""

# Insert before the closing brace of the settings struct
# Find the last struct member
if "pwc" not in content:
    # Find the closing of the Settings struct
    last_brace = content.rfind("};")
    content = content[:last_brace] + pwc_settings + content[last_brace:]
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added PWC settings")
else:
    print("PWC settings already present")
