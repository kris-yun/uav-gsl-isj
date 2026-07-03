path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp"
with open(path) as f:
    content = f.read()

# Add debug logging to PWC init - always log, not just when enabled
old = """            if (pcfg.enabled) {
                GSL_INFO("[PWC] INITIALIZED enabled={} alpha={} beta={} max_corr={}",
                         pcfg.enabled, pcfg.alpha, pcfg.beta, pcfg.max_correction);
            }"""

new = """            GSL_INFO("[PWC] INIT enabled={} alpha={} beta={} max_corr={} log={}",
                     pcfg.enabled, pcfg.alpha, pcfg.beta, pcfg.max_correction, pcfg.log_file);"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added PWC debug logging")
else:
    print("Pattern not found")
