#!/usr/bin/env python3
"""Fix OPGSL.hpp: move EDPA declarations inside the class"""
hpp = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp"

with open(hpp, "r") as f:
    content = f.read()

# Find EDPA block outside class
edpa_start = content.find("    // EDPA-GSL Layer 1")
ns_end = content.find("} // namespace GSL")

if edpa_start > 0 and ns_end > edpa_start:
    edpa_block = content[edpa_start:ns_end]
    # Remove from current position
    content = content[:edpa_start] + content[ns_end:]
    
    # Find the class closing brace
    # Look for "selectBestHeight();" which is the last function before class end
    class_end_marker = "    float selectBestHeight();\n};"
    marker_pos = content.find("selectBestHeight();")
    if marker_pos > 0:
        # Find the closing brace after selectBestHeight
        brace_pos = content.find("};", marker_pos)
        if brace_pos > 0:
            content = content[:brace_pos] + "\n" + edpa_block + content[brace_pos:]
            with open(hpp, "w") as f:
                f.write(content)
            print("Fixed: EDPA declarations moved inside class")
        else:
            print("Could not find class closing brace")
    else:
        print("Could not find selectBestHeight marker")
else:
    print("EDPA block not found or already inside class")
