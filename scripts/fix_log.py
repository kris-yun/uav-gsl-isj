#!/usr/bin/env python3
path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path, "r") as f:
    c = f.read()
c = c.replace('e={:.1f}', 'log_e={:.2f}')
with open(path, "w") as f:
    f.write(c)
print("Fixed log message")
