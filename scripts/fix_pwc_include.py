path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.hpp"
with open(path) as f:
    content = f.read()

# Add include after the last #include
if "PwcCorrector.hpp" not in content:
    content = content.replace(
        '#include <gsl_server/core/ConditionalMacros.hpp>',
        '#include <gsl_server/core/ConditionalMacros.hpp>\n#include <gsl_server/pwc/PwcCorrector.hpp>'
    )
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added PwcCorrector.hpp include")
else:
    print("Already included")
