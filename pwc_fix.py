import sys
f = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp"
with open(f, "r") as fh:
    lines = fh.readlines()

# Find and comment out the old PWC init block in Initialize()
old_block_start = None
old_block_end = None
for i, line in enumerate(lines):
    if "// PWC: Initialize Plume Wind Correction (moved from processGasAndWindMeasurements)" in line:
        old_block_start = i
    if old_block_start and "pwcCorrector_ = std::make_unique" in line:
        old_block_end = i + 1
        # Find the closing of the block
        for j in range(i+1, min(i+5, len(lines))):
            if lines[j].strip() == "}" and "GSL_INFO" not in lines[j]:
                old_block_end = j + 1
                break
        break

if old_block_start and old_block_end:
    # Comment out old block
    for k in range(old_block_start, old_block_end):
        lines[k] = "// DISABLED_OLD_PWC: " + lines[k]
    print(f"Commented out old PWC init at lines {old_block_start+1}-{old_block_end}")
else:
    print(f"OLD BLOCK NOT FOUND (start={old_block_start}, end={old_block_end})")
    sys.exit(1)

# Find where pwc params are read (settings.pwc.enabled = getParam)
pwc_param_line = None
for i, line in enumerate(lines):
    if 'settings.pwc.enabled = getParam<bool>("pwc_enabled"' in line:
        pwc_param_line = i
        break

if pwc_param_line is None:
    print("PWC param line not found")
    sys.exit(1)

# Find end of PWC param block (settings.pwc.log_file)
pwc_params_end = None
for i in range(pwc_param_line, min(pwc_param_line + 15, len(lines))):
    if "settings.pwc.log_file" in lines[i]:
        pwc_params_end = i + 1
        break

if pwc_params_end is None:
    print("PWC params end not found")
    sys.exit(1)

# Insert PWC initialization after params
new_lines = [
    "\n        // PWC: Initialize after parameters are read\n",
    "        {\n",
    "            uav_gsl_pwc::Config pcfg;\n",
    "            pcfg.enabled = settings.pwc.enabled;\n",
    "            pcfg.beta = settings.pwc.beta;\n",
    "            pcfg.max_correction = settings.pwc.max_correction;\n",
    "            pcfg.min_wind = settings.pwc.min_wind;\n",
    "            pcfg.use_adaptive = settings.pwc.use_adaptive;\n",
    "            pcfg.plume_scale_factor = settings.pwc.plume_scale_factor;\n",
    "            pcfg.wind_vector_is_flow_to = settings.pwc.wind_vector_is_flow_to;\n",
    '            pcfg.log_file = settings.pwc.log_file;\n',
    "            pwcCorrector_ = std::make_unique<uav_gsl_pwc::PwcCorrector>(pcfg);\n",
    '            GSL_INFO("[PWC] Init (post-params) enabled={} beta={}", pcfg.enabled, pcfg.beta);\n',
    "        }\n",
]

for j, nl in enumerate(new_lines):
    lines.insert(pwc_params_end + j, nl)

with open(f, "w") as fh:
    fh.writelines(lines)
print(f"PWC init moved to after params (after line {pwc_params_end+1})")
