with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    content = f.read()

# Fix NBV: log_lik -> lambda (two occurrences in selectNBV)
content = content.replace(
    '                            float log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,\n                                                               wind_x, wind_y, wind_speed);\n                            mean_c += p * (1.0f - std::exp(-lambda));',
    '                            float lam = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,\n                                                               wind_x, wind_y, wind_speed);\n                            mean_c += p * (1.0f - std::exp(-lam));'
)

content = content.replace(
    '                            float log_lik = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,\n                                                               wind_x, wind_y, wind_speed);\n                            float c_pred = 1.0f - std::exp(-lambda);',
    '                            float lam = plumeLogLikelihood(sx, sy, sz, cx, cy, cz,\n                                                               wind_x, wind_y, wind_speed);\n                            float c_pred = 1.0f - std::exp(-lam);'
)

# Also fix EFE caller if needed
content = content.replace(
    'float lambda = posterior3d_.plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,\n                                                          current_altitude_, wx, wy, ws);',
    'float lam_efe = posterior3d_.plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,\n                                                          current_altitude_, wx, wy, ws);'
)
content = content.replace(
    'float cp = 1.0f - std::exp(-lambda);',
    'float cp = 1.0f - std::exp(-lam_efe);'
)

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(content)
print("Fixed lambda variable names")