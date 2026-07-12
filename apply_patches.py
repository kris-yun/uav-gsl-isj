import re

hpp_path = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp'
cpp_path = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'

# 1. Fix OPGSL.hpp: add SPRT include + member
with open(hpp_path, 'r') as f:
    hpp = f.read()

# Add SPRT include after CP_Stopping include
if 'SPRT_Stopping.hpp' not in hpp:
    hpp = hpp.replace('#include "CP_Stopping.hpp"', '#include "CP_Stopping.hpp"\n#include "SPRT_Stopping.hpp"')
    print('Added SPRT_Stopping.hpp include')

# Add SPRT member after cp_stopping_ member
if 'sprt_stopping_' not in hpp:
    hpp = hpp.replace('CP_Stopping cp_stopping_;', 'CP_Stopping cp_stopping_;\n        CP::SPRTStopping sprt_stopping_;')
    print('Added sprt_stopping_ member')

with open(hpp_path, 'w') as f:
    f.write(hpp)

# 2. Fix OPGSL.cpp: replace eta and convergence
with open(cpp_path, 'r') as f:
    cpp = f.read()

# Replace eta computation (find the kappa-driven block and replace)
old_eta = """    // === Kappa-driven Adaptive Eta (theoretically grounded) ==="""
new_eta = """    // === Kappa-driven Adaptive Eta with Exploration Floor ==="""
if old_eta in cpp:
    # Find the eta block - from the kappa comment to "float max_log"
    import re
    # Replace the entire eta block
    pattern = r'(    // === Kappa-driven.*?)(    float max_log)'
    replacement = """    // === Kappa-driven Adaptive Eta with Exploration Floor ===
    // Fix: early exploration needs higher eta to update posterior
    // Theory: Bissiri et al. (2016) allows any bounded predictable eta
    float eta;
    if (!use_adaptive_eta_) {
        eta = 0.5f;
    } else {
        float map_x, map_y, map_z;
        getMAP(map_x, map_y, map_z);
        float phi_map = poissonRate(map_x, map_y, cx, cy, wind_x, wind_y, wind_speed);
        phi_map = std::clamp(phi_map, 0.01f, 0.99f);
        float kappa_t = std::abs(std::log(phi_map / (1.0f - phi_map)));
        kappa_step_count_++;
        float alpha = kappa_ema_alpha_;
        if (kappa_step_count_ <= 10) alpha = 1.0f / kappa_step_count_;
        float diff = kappa_t - kappa_ema_mean_;
        kappa_ema_mean_ += alpha * diff;
        kappa_ema_var_ = (1.0f - alpha) * (kappa_ema_var_ + alpha * diff * diff);
        float kappa_std = std::sqrt(std::max(kappa_ema_var_, 0.01f));
        float z = (kappa_t - kappa_ema_mean_) / kappa_std;
        float kappa_eta = 1.0f / (1.0f + std::exp(-z));
        kappa_eta = std::clamp(kappa_eta, 0.05f, 0.95f);
        float exploration_floor = 0.4f * std::exp(-step_count_ / 40.0f);
        exploration_floor = std::max(exploration_floor, 0.05f);
        eta = std::max(kappa_eta, exploration_floor);
        eta = std::clamp(eta, 0.05f, 0.95f);
    }
    float dt_measure = 3.0f;

$2"""
    cpp = re.sub(pattern, replacement, cpp, flags=re.DOTALL)
    print('Replaced eta computation with exploration floor')

with open(cpp_path, 'w') as f:
    f.write(cpp)

print('Done - basic patches applied')
