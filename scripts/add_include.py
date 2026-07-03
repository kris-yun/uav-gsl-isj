path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp"
with open(path) as f:
    content = f.read()

old = '#include <gsl_server/algorithms/PMFS/PMFSViz.hpp>'
new = '''#include <gsl_server/algorithms/PMFS/PMFSViz.hpp>
#include <gsl_server/algorithms/PMFS/MovingStatePMFS.hpp>'''

if old in content and 'MovingStatePMFS.hpp' not in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added MovingStatePMFS.hpp include")
else:
    print("Already included or pattern not found")
