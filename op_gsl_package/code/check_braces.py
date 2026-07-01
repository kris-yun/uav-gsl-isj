import sys
with open("/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp") as f:
    lines = f.readlines()
depth = 0
for i, line in enumerate(lines, 1):
    for c in line:
        if c == "{": depth += 1
        if c == "}": depth -= 1
    if depth < 0 or i in [90,91,110,111,131,132,230,236,251,276,310,312,317,320,334,340,399,405,477,479,494,501,503,507,510,532,534,550,552,571,586,629,639,645,674,676,695,697]:
        print(f"Line {i}: depth={depth}  {line.rstrip()[:60]}")
print(f"Final depth at line {len(lines)}: {depth}")
