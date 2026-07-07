filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    content = f.read()

old_logic = '''        float R_t = computeCredibleRegionRadius();
        float log_delta = std::log(1.0f / cr_stopping_.delta);
        float contraction = cr_stopping_.prev_radius - R_t;
        if (contraction > 0) cr_stopping_.e_process += std::log1p(cr_stopping_.eta * contraction);
        cr_stopping_.prev_radius = R_t;'''

new_logic = '''        float R_t = computeCredibleRegionRadius();
        float log_delta = std::log(1.0f / cr_stopping_.delta);
        if (cr_stopping_.prev_radius < 0) {
            // First observation: initialize prev_radius, no e-process update
            cr_stopping_.prev_radius = R_t;
        } else {
            float contraction = cr_stopping_.prev_radius - R_t;
            if (contraction > 0) cr_stopping_.e_process += std::log1p(cr_stopping_.eta * contraction);
            cr_stopping_.prev_radius = R_t;
        }'''

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    print('Fixed e-process initialization logic')
else:
    print('ERROR: pattern not found')
    
with open(filepath, 'w') as f:
    f.write(content)
print('Done')
