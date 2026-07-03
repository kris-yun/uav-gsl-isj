# Add PWC member to PMFS.hpp
path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.hpp"
with open(path) as f:
    content = f.read()

# Add include
if "PwcCorrector.hpp" not in content:
    content = content.replace(
        "#include <gsl_server/wranf/WranfSupervisor.hpp>",
        "#include <gsl_server/wranf/WranfSupervisor.hpp>\n#include <gsl_server/pwc/PwcCorrector.hpp>"
    )

# Add member variable
if "pwcCorrector_" not in content:
    content = content.replace(
        "        double last_windDirection{0.0};",
        "        double last_windDirection{0.0};\n\n        // PWC: Plume Wind Correction\n        std::unique_ptr<uav_gsl_pwc::PwcCorrector> pwcCorrector_;"
    )

with open(path, 'w') as f:
    f.write(content)
print("OK: Added PWC to PMFS.hpp")
