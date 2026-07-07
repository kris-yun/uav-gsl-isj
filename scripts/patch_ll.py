# Read current file
with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    lines = f.readlines()

# Find the plumeLogLikelihood function boundaries
start_line = None
end_line = None
for i, line in enumerate(lines):
    if 'float OPGSL::SourcePosterior3D::plumeLogLikelihood' in line:
        start_line = i
    if start_line is not None and i > start_line and line.strip() == '}' and i < start_line + 80:
        end_line = i
        break

if start_line is None or end_line is None:
    print("ERROR: Could not find plumeLogLikelihood function boundaries")
    print("start_line=%s end_line=%s" % (start_line, end_line))
    import sys; sys.exit(1)

print("Found plumeLogLikelihood at lines %d-%d" % (start_line+1, end_line+1))

# New function: Poisson arrival rate model
new_func = '''// Poisson filament arrival model: lambda(x,s) = lambda0 * exp(-dist/ell) * (1 + alpha_w * cos_theta)
// Returns the ARRIVAL RATE (positive value), not log-likelihood.
// The binary event log-likelihood is computed in update() using:
//   detected:     log(1 - exp(-lambda * dt))
//   not detected: -lambda * dt
// This is physically motivated by GADEN filament dispersion model.
float OPGSL::SourcePosterior3D::plumeLogLikelihood(float sx, float sy, float sz,
                                                     float cx, float cy, float cz,
                                                     float wind_x, float wind_y, float wind_speed) const {
    float dx = cx - sx, dy = cy - sy, dz = cz - sz;
    float dist = std::sqrt(dx*dx + dy*dy + dz*dz);

    // Wind alignment: cos_theta > 0 when observation point is DOWNWIND of source candidate
    // (filaments drift downwind, so downwind positions see higher arrival rates)
    float wn = std::sqrt(wind_x*wind_x + wind_y*wind_y) + 1e-6f;
    float wx = wind_x / wn, wy = wind_y / wn;
    float cos_theta = (dx * wx + dy * wy) / (dist + 1e-6f);

    // Poisson arrival rate: exponential distance decay with wind modulation
    // lambda0: baseline rate at source (filaments/second)
    // ell: characteristic decay length (meters)
    // alpha_w: wind modulation strength (dimensionless)
    float lambda = poisson_lambda0_ * std::exp(-dist / poisson_ell_)
                   * (1.0f + poisson_alpha_w_ * cos_theta);
    lambda = std::max(lambda, 1e-6f);

    return lambda;
}
'''

# Replace lines start_line through end_line (inclusive)
lines[start_line:end_line+1] = [new_func]

with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.writelines(lines)

print("plumeLogLikelihood replaced with Poisson model successfully")