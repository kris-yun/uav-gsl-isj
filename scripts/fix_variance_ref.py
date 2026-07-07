path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS_utils.cpp"
with open(path) as f:
    content = f.read()

# Fix: compute variance locally instead of referencing the variable from checkSourceFound
old = "            // Estimate plume spread from probability map variance\n            double plume_spread = std::sqrt(variance);"
new = "            // Estimate plume spread from probability map variance\n            double local_variance = Utils::Variance(Grid2D<double>(sourceProbability, occupancy, gridMetadata));\n            double plume_spread = std::sqrt(local_variance);"

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Fixed variance reference")
else:
    print("Pattern not found")
