path = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/CP_Stopping.hpp'
with open(path) as f:
    code = f.read()

old = 'if (log_M_ >= log_threshold)\n            return true;\n\n        return false;\n    }'
new = 'if (log_M_ >= log_threshold)\n            return true;\n\n        if (stable_count_ >= cfg_.stable_req)\n            return true;\n\n        return false;\n    }'

if old in code:
    code = code.replace(old, new)
    with open(path, 'w') as f:
        f.write(code)
    print('Restored stable_count')
else:
    print('Pattern not found')