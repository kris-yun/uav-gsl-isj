filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    content = f.read()

# Find the update function and add mode switching
old_start = '''void OPGSL::SourcePosterior3D::update(float cx, float cy, float cz, float concentration,
                                       float wind_x, float wind_y, float wind_speed) {
    if (!initialized_) return;
    // Temporal decay
    float decay = 0.995f;
    for (int ii = 0; ii < nx_; ii++)
        for (int jj = 0; jj < ny_; jj++)
            for (int kk = 0; kk < nz_; kk++)
                grid[ii][jj][kk] *= decay;

    float max_log = -1e9f;
    
    // Event-driven model parameters (from EDPA config)
    // lambda(x, s) = lambda0 * exp(-||x-s||/ell) * (1 + alpha_w * cos(theta))
    // Detection probability: p_det = 1 - exp(-lambda * dt)
    const float lambda0 = 1.0f;   // source emission rate
    const float ell = 2.0f;       // characteristic transport length
    const float alpha_w = 0.5f;   // wind anisotropy
    const float dt = 1.0f;        // time step duration
    const float det_threshold = 0.01f;  // detection threshold
    bool detected = (concentration > det_threshold);'''

new_start = '''void OPGSL::SourcePosterior3D::update(float cx, float cy, float cz, float concentration,
                                       float wind_x, float wind_y, float wind_speed) {
    if (!initialized_) return;
    // Temporal decay
    float decay = 0.995f;
    for (int ii = 0; ii < nx_; ii++)
        for (int jj = 0; jj < ny_; jj++)
            for (int kk = 0; kk < nz_; kk++)
                grid[ii][jj][kk] *= decay;

    float max_log = -1e9f;
    
    // Event-driven model parameters
    const float lambda0 = 1.0f;
    const float ell = 2.0f;
    const float alpha_w = 0.5f;
    const float dt = 1.0f;
    const float det_threshold = 0.01f;
    bool detected = (concentration > det_threshold);
    bool use_event_driven = true;  // TODO: make this a parameter'''

if old_start in content:
    content = content.replace(old_start, new_start)
    print('Added use_event_driven flag (TODO: make parameter)')
else:
    print('Pattern not found, checking...')
    idx = content.find('bool detected = (concentration > det_threshold)')
    if idx >= 0:
        print(f'Found at {idx}, already has event-driven code')
    else:
        print('Event-driven code not found')

# Now add the parameter declaration
old_param = '    cr_stopping_.epsilon = getParam<float>("opgsl.edpa.stop_epsilon", 1.5f);'
new_param = '''    use_event_driven_posterior_ = getParam<bool>("opgsl.modules.event_driven", false);
    cr_stopping_.epsilon = getParam<float>("opgsl.edpa.stop_epsilon", 1.5f);'''

if old_param in content:
    content = content.replace(old_param, new_param)
    print('Added event_driven parameter')
else:
    print('Parameter pattern not found')

with open(filepath, 'w') as f:
    f.write(content)
print('Done')
