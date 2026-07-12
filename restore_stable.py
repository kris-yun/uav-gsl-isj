# Restore stable_count in shouldStop
path = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/CP_Stopping.hpp'
with open(path) as f:
    code = f.read()

old = """    bool shouldStop() const {
        if (post_warmup_count_ < cfg_.min_steps)
            return false;

        float log_threshold = -std::log(cfg_.delta);
        if (log_M_ >= log_threshold)
            return true;

        return false;
    }"""

new = """    bool shouldStop() const {
        if (post_warmup_count_ < cfg_.min_steps)
            return false;

        float log_threshold = -std::log(cfg_.delta);
        if (log_M_ >= log_threshold)
            return true;

        if (stable_count_ >= cfg_.stable_req)
            return true;

        return false;
    }"""

if old in code:
    code = code.replace(old, new)
    with open(path, 'w') as f:
        f.write(code)
    print('Restored stable_count')
else:
    print('Pattern not found')
