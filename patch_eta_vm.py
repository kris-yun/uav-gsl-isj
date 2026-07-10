# -*- coding: utf-8 -*-
with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    lines = f.readlines()

# Find the eta computation block (lines 385-399 approximately)
start_line = None
end_line = None
for i, line in enumerate(lines):
    if 'eta = 0.6f + 0.3f * wind_confidence_' in line:
        # Find the float eta; declaration before it
        for j in range(max(0, i-10), i):
            if 'float eta;' in lines[j]:
                start_line = j
                break
        end_line = i + 1  # include the else block
        break

if start_line is None:
    print('ERROR: Could not find eta computation block')
    exit(1)

print(f'Found eta block at lines {start_line+1}-{end_line+1}')

# Find the full block: from "float eta;" to the closing of the else
# Let's find from "// eta -> 1:" to the line after "eta = 0.15f + 0.35f"
for i in range(max(0, start_line-10), start_line):
    if '// eta -> 1:' in lines[i]:
        start_line = i
        break

# Find end: after "eta = 0.15f + 0.35f * wind_confidence_"
for i in range(end_line, min(end_line+5, len(lines))):
    if '0.15f + 0.35f' in lines[i]:
        end_line = i + 1
        break

print(f'Replacing lines {start_line+1} to {end_line}')
print('Old content:')
for i in range(start_line, end_line):
    print(f'  {i+1}: {lines[i].rstrip()}')

# New eta computation
new_lines = [
    '// Regret-based adaptive eta (Grunwald & van Ommen, 2017)\n',
    '// eta = 1/(1 + gamma_hat), gamma_hat = EMA of empirical mixability gap\n',
    'float eta;\n',
    'if (!use_adaptive_eta_) {\n',
    '    eta = 0.5f;  // Fixed eta for ablation\n',
    '} else {\n',
    '    float gamma_inst;\n',
    '    if (detected) {\n',
    '        gamma_inst = 0.3f * (1.0f - wind_confidence_);\n',
    '    } else {\n',
    '        gamma_inst = 2.0f + 1.5f * (1.0f - wind_confidence_);\n',
    '    }\n',
    '    cumulative_regret_ = (1.0f - regret_ema_lambda_) * cumulative_regret_\n',
    '                       + regret_ema_lambda_ * gamma_inst;\n',
    '    regret_step_count_++;\n',
    '    eta = 1.0f / (1.0f + cumulative_regret_);\n',
    '    eta = std::clamp(eta, 0.1f, 0.95f);\n',
    '}\n',
]

lines[start_line:end_line] = new_lines

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.writelines(lines)

print('SUCCESS: Eta computation replaced with regret-based version')
