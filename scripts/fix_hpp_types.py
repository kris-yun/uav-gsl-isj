filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp"
with open(filepath, 'r') as f:
    content = f.read()

content = content.replace("CP::OnlineConformalStopping cp_stopping_;", "CP::EProcessStopping cp_stopping_;")

with open(filepath, 'w') as f:
    f.write(content)
print("OPGSL.hpp patched")