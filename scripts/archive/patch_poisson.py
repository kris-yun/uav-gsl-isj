import sys

path = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(path, 'r') as f:
    lines = f.readlines()

insert_after = None
for i, line in enumerate(lines):
    if 'return log_lik;' in line and i > 200:
        if i+1 < len(lines) and lines[i+1].strip() == '}':
            insert_after = i + 1
            break

if insert_after is None:
    print('ERROR: Could not find end of plumeLogLikelihood')
    sys.exit(1)

print(f'Found plumeLogLikelihood end at line {insert_after+1}')

poisson_rate_code = '''
float OPGSL::SourcePosterior3D::poissonRate(float sx, float sy, float cx, float cy,
                                             float wind_x, float wind_y, float wind_speed) const {
    float dx = cx - sx, dy = cy - sy;
    float dist = std::sqrt(dx*dx + dy*dy);
    float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y);
    float spatial = std::exp(-dist / arrival_rate_ell_);
    float wind_mod = 1.0f;
    if (wn > 0.05f && dist > 0.01f) {
        float cos_theta = (dx * wind_x + dy * wind_y) / (dist * wn);
        wind_mod = 1.0f + arrival_rate_alphaw_ * cos_theta;
        wind_mod = std::max(wind_mod, 0.1f);
    }
    return arrival_rate_lambda0_ * spatial * wind_mod;
}

void OPGSL::SourcePosterior3D::binaryEventUpdate(float cx, float cy, float cz,
                                                   float concentration, float detection_threshold,
                                                   float wind_x, float wind_y, float wind_speed) {
    if (!initialized_) return;
    bool detected = (concentration > detection_threshold);
    float decay = 0.998f;
    for (int ii = 0; ii < nx_; ii++)
        for (int jj = 0; jj < ny_; jj++)
            for (int kk = 0; kk < nz_; kk++)
                grid[ii][jj][kk] *= decay;
    float max_log = -1e9f;
    float dt_measure = 3.0f;
    for (int i = 0; i < nx_; i++) {
        for (int j = 0; j < ny_; j++) {
            for (int k = 0; k < nz_; k++) {
                float sx = x_min_ + (i+0.5f) * dx_;
                float sy = y_min_ + (j+0.5f) * dy_;
                float lam = poissonRate(sx, sy, cx, cy, wind_x, wind_y, wind_speed);
                float lam_dt = lam * dt_measure;
                float log_lik;
                if (detected) {
                    float neg_lam_dt = -lam_dt;
                    if (neg_lam_dt < -20.0f) {
                        log_lik = 0.0f;
                    } else {
                        log_lik = std::log1p(-std::exp(neg_lam_dt));
                    }
                } else {
                    log_lik = -lam_dt;
                }
                grid[i][j][k] += log_lik;
                if (grid[i][j][k] > max_log) max_log = grid[i][j][k];
            }
        }
    }
    float log_sum = -1e9f;
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++) {
                grid[i][j][k] -= max_log;
                log_sum = std::log(std::exp(log_sum) + std::exp(grid[i][j][k]));
            }
    for (int i = 0; i < nx_; i++)
        for (int j = 0; j < ny_; j++)
            for (int k = 0; k < nz_; k++)
                grid[i][j][k] -= log_sum;
}
'''

lines.insert(insert_after + 1, poisson_rate_code)
print(f'Inserted poissonRate + binaryEventUpdate after line {insert_after+1}')

param_insert = None
for i, line in enumerate(lines):
    if 'opgsl.modules.upwind_tracking' in line and 'getParam' in line:
        param_insert = i
        break

if param_insert:
    event_params = '    // Event-driven binary model parameters (Poisson filament arrival)\n'
    event_params += '    use_event_driven_posterior_ = getParam<bool>("opgsl.event_driven.enabled", false);\n'
    event_params += '    detection_threshold_ = getParam<float>("opgsl.event_driven.detection_threshold", 0.01f);\n'
    event_params += '    arrival_rate_lambda0_ = getParam<float>("opgsl.event_driven.lambda0", 2.0f);\n'
    event_params += '    arrival_rate_ell_ = getParam<float>("opgsl.event_driven.ell", 3.0f);\n'
    event_params += '    arrival_rate_alphaw_ = getParam<float>("opgsl.event_driven.alpha_w", 0.5f);\n'
    event_params += '    use_edpa_ = getParam<bool>("opgsl.edpa.enabled", false);\n'
    event_params += '    GSL_INFO("Event-driven model: enabled={} lambda0={:.1f} ell={:.1f} alpha_w={:.2f} threshold={:.3f}",\n'
    event_params += '             use_event_driven_posterior_, arrival_rate_lambda0_, arrival_rate_ell_, arrival_rate_alphaw_, detection_threshold_);\n'
    lines.insert(param_insert, event_params + '\n')
    print(f'Inserted event-driven params at line {param_insert+1}')

for i, line in enumerate(lines):
    if 'void OPGSL::SourcePosterior3D::update(' in line and i > 300:
        for j in range(i, min(i+5, len(lines))):
            if 'if (!initialized_) return;' in lines[j]:
                dispatch_code = '    // Dispatch to binary event model if enabled\n'
                dispatch_code += '    if (use_event_driven_posterior_) {\n'
                dispatch_code += '        binaryEventUpdate(cx, cy, cz, concentration, detection_threshold_, wind_x, wind_y, wind_speed);\n'
                dispatch_code += '        return;\n'
                dispatch_code += '    }\n'
                lines.insert(j+1, dispatch_code)
                print(f'Inserted binary dispatch at line {j+2}')
                break
        break

with open(path, 'w') as f:
    f.writelines(lines)

print('DONE: Poisson binary event model implemented')
