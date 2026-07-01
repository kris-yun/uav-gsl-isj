path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path) as f:
    code = f.read()

# Fix EFE block: replace direct member access with posterior3d_. access
# and use correct wind variable names (wx, wy, ws from sdnbvStep)

fixes = [
    ('float cand_x = std::clamp(center_x + fdx, x_min_ + 0.5f, x_max_ - 0.5f);',
     'float cand_x = std::clamp(center_x + fdx, posterior3d_.x_min_ + 0.5f, posterior3d_.x_max_ - 0.5f);'),
    ('float cand_y = std::clamp(center_y + fdy, y_min_ + 0.5f, y_max_ - 0.5f);',
     'float cand_y = std::clamp(center_y + fdy, posterior3d_.y_min_ + 0.5f, posterior3d_.y_max_ - 0.5f);'),
    ('for (int ii = 0; ii < nx_; ii += 2) {',
     'for (int ii = 0; ii < posterior3d_.nx_; ii += 2) {'),
    ('for (int jj = 0; jj < ny_; jj += 2) {',
     'for (int jj = 0; jj < posterior3d_.ny_; jj += 2) {'),
    ('for (int kk = 0; kk < nz_; kk += 2) {',
     'for (int kk = 0; kk < posterior3d_.nz_; kk += 2) {'),
    ('float psx = x_min_ + (ii+0.5f) * dx_;',
     'float psx = posterior3d_.x_min_ + (ii+0.5f) * posterior3d_.dx_;'),
    ('float psy = y_min_ + (jj+0.5f) * dy_;',
     'float psy = posterior3d_.y_min_ + (jj+0.5f) * posterior3d_.dy_;'),
    ('float psz = z_min_ + (kk+0.5f) * dz_;',
     'float psz = posterior3d_.z_min_ + (kk+0.5f) * posterior3d_.dz_;'),
    ('float p = std::exp(grid[ii][jj][kk]);',
     'float p = std::exp(posterior3d_.grid[ii][jj][kk]);'),
    ('float ll = plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,',
     'float ll = posterior3d_.plumeLogLikelihood(psx, psy, psz, cand_x, cand_y,'),
    ('current_altitude_, wind_x, wind_y, wind_speed);',
     'current_altitude_, wx, wy, ws);'),
]

for old, new in fixes:
    if old in code:
        code = code.replace(old, new)
    else:
        print(f"SKIP: {old[:60]}...")

with open(path, 'w') as f:
    f.write(code)
print("EFE scope fixes applied")