import re

filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(filepath, 'r') as f:
    content = f.read()

# Fix line 86: StoppingConfig -> EProcessConfig
content = content.replace("CP::StoppingConfig cp_cfg;", "CP::EProcessConfig cp_cfg;")

# Fix line 90: OnlineConformalStopping -> EProcessStopping
content = content.replace("CP::OnlineConformalStopping(cp_cfg)", "CP::EProcessStopping(cp_cfg)")

# Fix config field names
content = content.replace("cp_cfg.alpha =", "cp_cfg.delta =")
content = content.replace("cp_cfg.w_thresh =", "cp_cfg.convergence_thresh =")

# Fix log message references
content = content.replace("cp_stopping_.getWidth()", "cp_stopping_.getWidth()")

with open(filepath, 'w') as f:
    f.write(content)
print("OPGSL.cpp patched")