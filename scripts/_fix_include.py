with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/RwgfSupervisor.cpp','r') as f:
    content = f.read()
content = content.replace('#include "RwgfSupervisor.hpp"', '#include <gsl_server/wranf/RwgfSupervisor.hpp>')
with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/RwgfSupervisor.cpp','w') as f:
    f.write(content)
print('fixed')
