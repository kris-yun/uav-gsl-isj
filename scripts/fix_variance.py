path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp"
with open(path) as f:
    content = f.read()

# Replace Utils::Variance call with 0.0 (not used by WRANF)
old = "win.server_variance = Utils::Variance(Grid2D<double>(pmfs->sourceProbability, pmfs->occupancy, pmfs->gridMetadata));"
new = "win.server_variance = 0.0;  // not used by WRANF"

count = content.count(old)
content = content.replace(old, new)

with open(path, 'w') as f:
    f.write(content)
print(f"Replaced {count} occurrences of Utils::Variance")
