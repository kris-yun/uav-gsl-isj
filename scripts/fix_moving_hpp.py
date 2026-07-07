path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.hpp"
with open(path) as f:
    content = f.read()

# Add WRANF include
content = content.replace(
    '#include <gsl_server/core/Vectors.hpp>',
    '#include <gsl_server/core/Vectors.hpp>\n#include <gsl_server/wranf/WranfSupervisor.hpp>\n#include <memory>'
)

# Add WRANF member before Publishers struct
content = content.replace(
    '        struct Publishers',
    '''        // WRANF Supervisor
        std::unique_ptr<uav_gsl_wranf::WranfSupervisor> wranfSupervisor_;
        int wranfStep_ = 0;

        struct Publishers'''
)

with open(path, 'w') as f:
    f.write(content)

# Verify
with open(path) as f:
    c = f.read()
print(f"wranfSupervisor_ in header: {'wranfSupervisor_' in c}")
print(f"WranfSupervisor.hpp included: {'WranfSupervisor.hpp' in c}")
