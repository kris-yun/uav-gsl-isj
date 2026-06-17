f = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.hpp"
with open(f, "r") as fh:
    content = fh.read()
content = content.replace(
    "std::vector<double> cfar_window_  // CFAR sliding window;",
    "std::vector<double> cfar_window_;  // CFAR sliding window"
)
with open(f, "w") as fh:
    fh.write(content)
print("HPP_FIXED")
