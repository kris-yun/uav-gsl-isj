with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    content = f.read()

# Fix: posterior grid must cover the environment including source at (5.0, 6.2)
# Original: init(-7.5, 3.9, -7.9, 0.82, ...) — source is OUTSIDE
# Fixed: init(-1.0, 11.0, -1.0, 11.0, ...) — covers full 10x10m environment
old = 'posterior3d_.init(-7.5f, 3.9f, -7.9f, 0.82f, z_min_, z_max_);'
new = 'posterior3d_.init(-1.0f, 11.0f, -1.0f, 11.0f, z_min_, z_max_);'

if old in content:
    content = content.replace(old, new)
    print("Fixed posterior grid: [-1,11] x [-1,11] (covers source at 5.0,6.2)")
else:
    print("WARNING: init pattern not found")
    # Try to find it
    import re
    m = re.search(r'posterior3d_\.init\([^)]+\)', content)
    if m:
        print("  Found: %s" % m.group())

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(content)