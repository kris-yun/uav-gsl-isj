with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    content = f.read()

# Fix remaining exp(ll) -> detection probability
content = content.replace('float cp = std::exp(ll);', 'float cp = 1.0f - std::exp(-lam_e);')

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(content)
print("Fixed EFE caller")