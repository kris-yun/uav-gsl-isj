#!/usr/bin/env python3
# Fix epsilon to 0.5m in OPGSL.cpp
path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path, "r") as f:
    c = f.read()

# Fix epsilon in struct default
c = c.replace("float epsilon=1.5f", "float epsilon=0.5f")

# Fix epsilon in parameter reading
import re
c = re.sub(r'stop_epsilon.*?\)', 'stop_epsilon", 0.5f)', c)

with open(path, "w") as f:
    f.write(c)

# Verify
with open(path, "r") as f:
    for line in f:
        if "epsilon" in line.lower():
            print(line.strip())
