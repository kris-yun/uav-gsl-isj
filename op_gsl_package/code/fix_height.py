# Fix: Reset GP on CALIBRATE->TRACK transition + lower GP weight
import sys
sys.stdout.reconfigure(encoding="utf-8")

CPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
HPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp"

with open(CPP, "r") as f:
    cpp = f.read()
with open(HPP, "r") as f:
    hpp = f.read()

# Fix 1: Reset GP when entering TRACK phase (after calibration)
# Find the line "alt_phase_ = AltPhase::TRACK;" in processCalibrationMeasurement
old_track_transition = "        alt_phase_ = AltPhase::TRACK;\n        if (use_gp_altitude_) gp_.reset(best_calibrated_z_, z_min_, z_max_);"
if old_track_transition in cpp:
    # Already has gp_.reset - good
    print("CPP: GP reset on TRACK transition already exists")
else:
    # Find and add GP reset
    old_calib_done = "        calibration_active_ = false;\n        alt_phase_ = AltPhase::TRACK;"
    new_calib_done = """        calibration_active_ = false;
        alt_phase_ = AltPhase::TRACK;
        // CRITICAL: Reset GP with calibration best z, clear old explore-phase data
        if (use_gp_altitude_) {
            gp_.reset(best_calibrated_z_, z_min_, z_max_);
            // Pre-seed GP with calibration observations
            for (const auto& lp : layer_profile_) {
                if (lp.concentration > 0.01f) {
                    gp_.addObs(lp.z, lp.concentration);
                }
            }
        }"""
    if old_calib_done in cpp:
        cpp = cpp.replace(old_calib_done, new_calib_done)
        print("CPP: Added GP reset + calibration pre-seeding on TRACK transition")
    else:
        print("WARN: Could not find calibration_done block")

# Fix 2: Lower GP weight in getNextZAnchored
old_weight = "            float gp_weight = std::min(0.3f, 0.1f + 0.02f * (float)n);"
new_weight = "            // Lower GP weight: calibration data is more reliable than GP\n            float gp_weight = std::min(0.15f, 0.05f + 0.01f * (float)n);"
if old_weight in hpp:
    hpp = hpp.replace(old_weight, new_weight)
    print("HPP: GP weight lowered (max 15%)")
else:
    print("WARN: Could not find gp_weight")

# Fix 3: Also reset GP when entering EXPLORE from TRACK (miss-triggered reset)
old_miss_reset = """                GSL_INFO("OPGSL: {} misses -> EXPLORE (cooldown)", consecutive_misses_);
                alt_phase_ = AltPhase::EXPLORE;
                calibration_cooldown_ = calibration_cooldown_duration_;
                gas_hit_count_ = 0;"""
new_miss_reset = """                GSL_INFO("OPGSL: {} misses -> EXPLORE (cooldown)", consecutive_misses_);
                alt_phase_ = AltPhase::EXPLORE;
                calibration_cooldown_ = calibration_cooldown_duration_;
                gas_hit_count_ = 0;
                // Reset GP when leaving TRACK (stale data)
                if (use_gp_altitude_) gp_.reset(current_altitude_, z_min_, z_max_);"""
if old_miss_reset in cpp:
    cpp = cpp.replace(old_miss_reset, new_miss_reset)
    print("CPP: Added GP reset on TRACK->EXPLORE transition")

with open(CPP, "w") as f:
    f.write(cpp)
with open(HPP, "w") as f:
    f.write(hpp)
print("All height fixes applied")
