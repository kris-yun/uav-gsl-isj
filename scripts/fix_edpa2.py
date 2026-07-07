#!/usr/bin/env python3
path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path, "r") as f:
    c = f.read()

# Fix 1: Increase search radius
c = c.replace("float search_radius = 2.0f;", "float search_radius = 5.0f;")

# Fix 2: Increase candidates
c = c.replace("int n_cand = 12;", "int n_cand = 24;")

# Fix 3: Increase wind modulation
c = c.replace("arrival_rate_alphaw_=0.5f", "arrival_rate_alphaw_=0.8f")

# Fix 4: Add fallback exploration
old = '        GSL_INFO("EDPA-SEARCH'
if "EDPA-FALLBACK" not in c:
    # Find the EDPA-SEARCH line and add fallback before it
    lines = c.split("\n")
    new_lines = []
    for i, line in enumerate(lines):
        if 'EDPA-SEARCH' in line and 'best_x' in line:
            # Add fallback logic before this line
            indent = "        "
            new_lines.append(indent + '// Fallback: if no gas, explore downwind')
            new_lines.append(indent + 'if (latest_gas_ < 0.005f && ws > 0.05f && step_count_ > 10) {')
            new_lines.append(indent + '    float wn = std::sqrt(wx*wx + wy*wy);')
            new_lines.append(indent + '    float explore_x = cx + 3.0f * wx / wn;')
            new_lines.append(indent + '    float explore_y = cy + 3.0f * wy / wn;')
            new_lines.append(indent + '    clipToMapBounds(explore_x, explore_y);')
            new_lines.append(indent + '    best_x = explore_x; best_y = explore_y;')
            new_lines.append(indent + '    GSL_INFO("EDPA-FALLBACK: downwind ({:.2f},{:.2f}) ws={:.2f}", best_x, best_y, ws);')
            new_lines.append(indent + '} else {')
            new_lines.append(indent + '    best_x = eig_r.x; best_y = eig_r.y;')
            new_lines.append(indent + '    clipToMapBounds(best_x, best_y);')
        new_lines.append(line)
        if 'EDPA-SEARCH' in line and 'step' in line:
            new_lines.append(indent + '}')
    c = "\n".join(new_lines)

with open(path, "w") as f:
    f.write(c)
print("Fixed EDPA-GSL: radius=5, n_cand=24, alphaw=0.8, fallback added")
