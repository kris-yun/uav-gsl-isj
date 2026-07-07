filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(filepath) as f:
    lines = f.readlines()

# Find "void OPGSL::computeEIGField" and add closing brace before it
for i, line in enumerate(lines):
    if "void OPGSL::computeEIGField" in line:
        # Check if previous line is already a closing brace
        if lines[i-1].strip() == "}":
            # Need to add another closing brace
            lines.insert(i, "}\n")
            print(f"Added closing brace at line {i}")
        break

with open(filepath, "w") as f:
    f.writelines(lines)
print("FIX SUCCESS")
