# Fix GP observation filtering and UCB parameters
import sys
sys.stdout.reconfigure(encoding="utf-8")

CPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
HPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp"

with open(CPP, "r") as f:
    cpp = f.read()
with open(HPP, "r") as f:
    hpp = f.read()

# Fix 1: HPP - Reduce UCB beta for less aggressive exploration
# Change beta from 2*log(n+1) to 0.5*log(n+1)
old_beta = "float beta = std::max(2.0f, 2.0f * std::log((float)n + 1.0f));"
new_beta = "float beta = std::max(0.5f, 0.5f * std::log((float)n + 1.0f));"
if old_beta in hpp:
    hpp = hpp.replace(old_beta, new_beta)
    print("HPP: UCB beta reduced (0.5*log)")
else:
    print("WARN: Could not find UCB beta in HPP")

# Fix 2: HPP - Add calibration anchoring to getNextZ()
# After getting UCB best_z, blend with calibration best
old_getNextZ_end = """            return best_z;
        }

        void reset("""
new_getNextZ_end = """            return best_z;
        }

        float getNextZAnchored(float calib_z) {
            float gp_z = getNextZ();
            // Blend: 70% calibration anchor + 30% GP (prevents UCB drift)
            // As more observations arrive, gradually trust GP more
            int n = (int)obs.size();
            float gp_weight = std::min(0.3f, 0.1f + 0.02f * (float)n);
            return calib_z * (1.0f - gp_weight) + gp_z * gp_weight;
        }

        void reset("""
if old_getNextZ_end in hpp:
    hpp = hpp.replace(old_getNextZ_end, new_getNextZ_end)
    print("HPP: Added getNextZAnchored()")
else:
    print("WARN: Could not find getNextZ return in HPP")

# Fix 3: CPP - Use anchored version in TRACK phase
old_track = """        case AltPhase::TRACK: {
            if (use_gp_altitude_) {
                z_target = gp_.getNextZ();"""
new_track = """        case AltPhase::TRACK: {
            if (use_gp_altitude_) {
                z_target = gp_.getNextZAnchored(best_calibrated_z_);"""
if old_track in cpp:
    cpp = cpp.replace(old_track, new_track)
    print("CPP: TRACK phase uses anchored GP")
else:
    print("WARN: Could not find TRACK block in CPP")

# Fix 4: CPP - Only add GP observations near the source estimate (field peak)
# Replace the EXPLORE phase GP observation with proximity-gated version
old_explore_obs = """            // Also feed observations to GP during explore
            if (use_gp_altitude_ && latest_gas_ > 0.001f) {
                gp_.addObs(current_altitude_, latest_gas_);
            }"""
new_explore_obs = """            // Feed observations to GP only when near gas source estimate
            if (use_gp_altitude_ && latest_gas_ > 0.05f) {
                auto fld = field_estimator_.computeField();
                float dx = currentRobotPosition.x - fld.peak_x;
                float dy = currentRobotPosition.y - fld.peak_y;
                float dist_to_peak = std::sqrt(dx*dx + dy*dy);
                if (dist_to_peak < 2.0f) {
                    gp_.addObs(current_altitude_, latest_gas_);
                }
            }"""
if old_explore_obs in cpp:
    cpp = cpp.replace(old_explore_obs, new_explore_obs)
    print("CPP: EXPLORE GP obs gated by proximity")
else:
    print("WARN: Could not find EXPLORE GP obs in CPP")

# Fix 5: CPP - Also gate TRACK phase observations
old_track_obs = """    // BO+GP: add observation to Gaussian Process
    if (alt_phase_ == AltPhase::TRACK && use_gp_altitude_) {
        gp_.addObs(current_altitude_, latest_gas_);
    }"""
new_track_obs = """    // BO+GP: add observation only near source estimate with significant concentration
    if (alt_phase_ == AltPhase::TRACK && use_gp_altitude_ && latest_gas_ > 0.02f) {
        auto fld2 = field_estimator_.computeField();
        float dx2 = currentRobotPosition.x - fld2.peak_x;
        float dy2 = currentRobotPosition.y - fld2.peak_y;
        float dist2 = std::sqrt(dx2*dx2 + dy2*dy2);
        if (dist2 < 2.5f) {
            gp_.addObs(current_altitude_, latest_gas_);
        }
    }"""
if old_track_obs in cpp:
    cpp = cpp.replace(old_track_obs, new_track_obs)
    print("CPP: TRACK GP obs gated by proximity+concentration")
else:
    print("WARN: Could not find TRACK GP obs block in CPP")

# Fix 6: CPP - Also gate CALIBRATE phase observations  
old_calib_obs = """            // Feed calibration observations to GP
            if (use_gp_altitude_ && latest_gas_ > 0.001f) {
                gp_.addObs(current_altitude_, latest_gas_);
            }"""
new_calib_obs = """            // Feed calibration observations to GP (always during calibration - we're at source location)
            if (use_gp_altitude_ && latest_gas_ > 0.01f) {
                gp_.addObs(current_altitude_, latest_gas_);
            }"""
if old_calib_obs in cpp:
    cpp = cpp.replace(old_calib_obs, new_calib_obs)
    print("CPP: CALIBRATE GP obs threshold raised")

# Fix 7: HPP - Reduce GP sigma_n for less smoothing
old_sigma_n = "float sigma_n = 0.1f;"
new_sigma_n = "float sigma_n = 0.05f;"
if old_sigma_n in hpp:
    hpp = hpp.replace(old_sigma_n, new_sigma_n)
    print("HPP: sigma_n reduced to 0.05")

with open(CPP, "w") as f:
    f.write(cpp)
with open(HPP, "w") as f:
    f.write(hpp)
print("\nAll fixes applied. Build with colcon.")
