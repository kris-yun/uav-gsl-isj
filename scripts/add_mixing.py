with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    lines = f.readlines()

# Find and replace lines 279-290 (the normalization block)
# Line 279: "    // Log-sum-exp normalization"
# Through line 290: "                grid[i][j][k] -= log_sum;"
start = None
end = None
for i, line in enumerate(lines):
    if 'Log-sum-exp normalization' in line:
        start = i
    if start is not None and i > start and 'grid[i][j][k] -= log_sum;' in line:
        end = i
        break

if start is None or end is None:
    print("ERROR: Could not find normalization block at lines 279-290")
    import sys; sys.exit(1)

print("Found normalization at lines %d-%d" % (start+1, end+1))

new_block = [
    '    // Log-sum-exp normalization with uniform mixing (prevents posterior collapse)\n',
    '    float mix_alpha = 0.02f;\n',
    '    float log_mix = std::log(mix_alpha / (float)(nx_ * ny_ * nz_));\n',
    '    float log_1m_mix = std::log(1.0f - mix_alpha);\n',
    '    float log_sum = -1e9f;\n',
    '    for (int i = 0; i < nx_; i++)\n',
    '        for (int j = 0; j < ny_; j++)\n',
    '            for (int k = 0; k < nz_; k++) {\n',
    '                grid[i][j][k] -= max_log;\n',
    '                grid[i][j][k] = log_1m_mix + grid[i][j][k];\n',
    '                float u = log_mix;\n',
    '                float v = grid[i][j][k];\n',
    '                float mx2 = (u > v) ? u : v;\n',
    '                grid[i][j][k] = mx2 + std::log(std::exp(u - mx2) + std::exp(v - mx2));\n',
    '                log_sum = std::log(std::exp(log_sum) + std::exp(grid[i][j][k]));\n',
    '            }\n',
    '    for (int i = 0; i < nx_; i++)\n',
    '        for (int j = 0; j < ny_; j++)\n',
    '            for (int k = 0; k < nz_; k++)\n',
    '                grid[i][j][k] -= log_sum;\n',
]

lines[start:end+1] = new_block

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.writelines(lines)

# Verify brace balance
content = ''.join(lines)
opens = content.count('{')
closes = content.count('}')
print("Braces: open=%d close=%d" % (opens, closes))
print("Mixing block inserted OK")