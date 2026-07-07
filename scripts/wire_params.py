filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    content = f.read()

# Replace hardcoded event-driven parameters with member variables
old_params = '''    // Event-driven model parameters
    const float lambda0 = 1.0f;
    const float ell = 2.0f;
    const float alpha_w = 0.5f;
    const float dt = 1.0f;
    const float det_threshold = 0.01f;
    bool detected = (concentration > det_threshold);
    bool use_event_driven = true;'''

new_params = '''    // Event-driven model parameters (from OPGSL member variables)
    const float lambda0 = arrival_rate_lambda0_;
    const float ell = arrival_rate_ell_;
    const float alpha_w = arrival_rate_alphaw_;
    const float dt = 1.0f;
    const float det_threshold = detection_threshold_;
    bool detected = (concentration > det_threshold);
    bool use_event_driven = true;'''

if old_params in content:
    content = content.replace(old_params, new_params)
    with open(filepath, 'w') as f:
        f.write(content)
    print('Updated to use member variables for event-driven params')
else:
    # Try without the use_event_driven line
    old_params2 = '''    const float lambda0 = 1.0f;
    const float ell = 2.0f;
    const float alpha_w = 0.5f;
    const float dt = 1.0f;
    const float det_threshold = 0.01f;'''
    
    new_params2 = '''    const float lambda0 = arrival_rate_lambda0_;
    const float ell = arrival_rate_ell_;
    const float alpha_w = arrival_rate_alphaw_;
    const float dt = 1.0f;
    const float det_threshold = detection_threshold_;'''
    
    if old_params2 in content:
        content = content.replace(old_params2, new_params2)
        with open(filepath, 'w') as f:
            f.write(content)
        print('Updated (alt pattern) to use member variables')
    else:
        print('Pattern not found, checking...')
        idx = content.find('const float lambda0')
        if idx >= 0:
            print(f'Found at {idx}: {content[idx:idx+100]}')
        else:
            print('lambda0 not found')
