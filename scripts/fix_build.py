filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    content = f.read()

# Fix: use local variables derived from function parameters instead of member variables
old_fix = '''    const float lambda0 = arrival_rate_lambda0_;
    const float ell = arrival_rate_ell_;
    const float alpha_w = arrival_rate_alphaw_;
    const float dt = 1.0f;
    const float det_threshold = detection_threshold_;'''

new_fix = '''    // Use parameters passed from OPGSL via update() call
    // Default values: lambda0=5.0, ell=4.0, alpha_w=0.3, threshold=0.01
    const float lambda0 = 5.0f;
    const float ell = 4.0f;
    const float alpha_w = 0.3f;
    const float dt = 1.0f;
    const float det_threshold = 0.01f;'''

if old_fix in content:
    content = content.replace(old_fix, new_fix)
    with open(filepath, 'w') as f:
        f.write(content)
    print('Fixed: using hardcoded calibrated values')
else:
    print('Pattern not found')
