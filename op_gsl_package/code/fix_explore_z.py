# Fix EXPLORE phase altitude: gentle sinusoidal scan instead of aggressive Levy
# Also raise z_min from 0.0 to 0.1
import sys
sys.stdout.reconfigure(encoding='utf-8')

CPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(CPP, "r") as f:
    content = f.read()

# Fix 1: EXPLORE phase - replace Levy with sinusoidal scan
old_explore = """        case AltPhase::EXPLORE: {
            if (use_levy_altitude_) {
                if (levy_height_step_remaining_ <= 0) {
                    levy_height_target_ = levyHeight(current_altitude_);
                    levy_height_step_remaining_ = std::uniform_int_distribution<int>(5, 10)(rng_);
                }
                levy_height_step_remaining_--;
                z_target = levy_height_target_;
            }
            break;
        }"""

new_explore = """        case AltPhase::EXPLORE: {
            // Gentle sinusoidal scan to collect diverse z-concentration observations for GP
            // Oscillates between 0.3m and 1.5m over ~20 step period
            float z_base = 0.3f;
            float z_amp = 0.6f;
            float period = 20.0f;
            z_target = z_base + z_amp * (1.0f + std::sin(2.0f * M_PI * (float)step_count_ / period)) / 2.0f;
            // Also feed observations to GP during explore
            if (use_gp_altitude_ && latest_gas_ > 0.001f) {
                gp_.addObs(current_altitude_, latest_gas_);
            }
            break;
        }"""

if old_explore in content:
    content = content.replace(old_explore, new_explore)
    print("EXPLORE phase fixed")
else:
    print("ERROR: Could not find EXPLORE block")
    sys.exit(1)

# Fix 2: Raise z_min from 0.0 to 0.1
content = content.replace(
    'z_min_ = getParam<double>("opgsl.altitude.z_min", 0.0);',
    'z_min_ = getParam<double>("opgsl.altitude.z_min", 0.1);'
)
# Also in HPP default
HPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp"
with open(HPP, "r") as f:
    hpp = f.read()
hpp = hpp.replace("float z_min = 0.0f;", "float z_min = 0.1f;")
with open(HPP, "w") as f:
    f.write(hpp)
print("z_min raised to 0.1")

# Fix 3: Also add GP observation during CALIBRATE phase for more data
old_calib = """        case AltPhase::CALIBRATE: {
            if (!calibration_z_sequence_.empty() && calibration_index_ < static_cast<int>(calibration_z_sequence_.size()))
                z_target = calibration_z_sequence_[calibration_index_];
            break;
        }"""

new_calib = """        case AltPhase::CALIBRATE: {
            if (!calibration_z_sequence_.empty() && calibration_index_ < static_cast<int>(calibration_z_sequence_.size()))
                z_target = calibration_z_sequence_[calibration_index_];
            // Feed calibration observations to GP
            if (use_gp_altitude_ && latest_gas_ > 0.001f) {
                gp_.addObs(current_altitude_, latest_gas_);
            }
            break;
        }"""

if old_calib in content:
    content = content.replace(old_calib, new_calib)
    print("CALIBRATE phase: GP observation added")

with open(CPP, "w") as f:
    f.write(content)
print("All fixes applied")
