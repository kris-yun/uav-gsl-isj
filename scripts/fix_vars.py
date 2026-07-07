with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    lines = f.readlines()

# Fix NBV caller: log_lik -> lam (line 410-411 and 422-423)
# Also fix lambda -> lam (lambda is C++ keyword)
fixes = 0
for i in range(len(lines)):
    if 'float log_lik = plumeLogLikelihood(' in lines[i] and i+1 < len(lines):
        lines[i] = lines[i].replace('float log_lik', 'float lam')
        fixes += 1
    if 'mean_c += p * (1.0f - std::exp(-lambda));' in lines[i]:
        lines[i] = lines[i].replace('-lambda)', '-lam)')
        fixes += 1
    if 'float c_pred = 1.0f - std::exp(-lambda);' in lines[i]:
        lines[i] = lines[i].replace('-lambda)', '-lam)')
        fixes += 1
    if 'float ll = posterior3d_.plumeLogLikelihood(' in lines[i]:
        lines[i] = lines[i].replace('float ll', 'float lam_e')
        fixes += 1
    if 'float cp = 1.0f - std::exp(-lambda);' in lines[i] or 'float cp = 1.0f - std::exp(-lam_e);' in lines[i]:
        lines[i] = '                            float cp = 1.0f - std::exp(-lam_e);\n'
        fixes += 1

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.writelines(lines)
print("Fixed %d variable names" % fixes)

# Verify
content = ''.join(lines)
opens = content.count('{')
closes = content.count('}')
print("Braces: open=%d close=%d balanced=%s" % (opens, closes, opens == closes))