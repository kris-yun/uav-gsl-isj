import sys
CPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(CPP, "r") as f:
    lines = f.readlines()
# Find line with "float dist = std::sqrt(dx*dx + dy*dy);" in infotaxisStep
for i, line in enumerate(lines):
    if "float dist = std::sqrt(dx*dx + dy*dy);" in line and i > 400:
        diag = '    GSL_INFO("DIAG_FIELD: peak=({:.2f},{:.2f}) robot=({:.2f},{:.2f}) dist={:.2f} entropy={:.2f} gas={:.4f}", ex, ey, cx, cy, dist, grad, latest_gas_);\n'
        lines.insert(i + 1, diag)
        print(f"Inserted diagnostic log after line {i+1}")
        break
with open(CPP, "w") as f:
    f.writelines(lines)
print("Done")
