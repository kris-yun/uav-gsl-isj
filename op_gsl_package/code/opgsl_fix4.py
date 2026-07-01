import re

CPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"

with open(CPP, "r") as f:
    c = f.read()

# Fix 1: HP filter - standard Krstic
c = c.replace(
    "eta = alpha_h * (eta + measurement - prev_y);",
    "eta = alpha_h * eta + (measurement - prev_y);  // standard Krstic form"
)

# Fix 2: ESC residual-based update
OLD_ESC = "if (alt_phase_ == AltPhase::TRACK && use_esc_altitude_) esc_.update(latest_gas_);"
NEW_ESC = """// Residual-based ESC: subtract field baseline to isolate altitude signal
    if (alt_phase_ == AltPhase::TRACK && use_esc_altitude_) {
        auto fld = field_estimator_.computeField();
        float gx = currentRobotPosition.x, gy = currentRobotPosition.y;
        int gi = static_cast<int>((gx + map_half_size_) / resolution_);
        int gj = static_cast<int>((gy + map_half_size_) / resolution_);
        gi = std::clamp(gi, 0, n_cells_ - 1);
        gj = std::clamp(gj, 0, n_cells_ - 1);
        float field_baseline = std::exp(fld.log_field(gi, gj));
        float residual = latest_gas_ - field_baseline;
        esc_.update(std::max(0.0f, residual));
    }"""
c = c.replace(OLD_ESC, NEW_ESC)

# Fix 3: Phase hysteresis cooldown
c = c.replace(
    "need_next_goal_ = true;",
    "if (calibration_cooldown_ > 0.0f) calibration_cooldown_ -= 1.0f;\n    need_next_goal_ = true;"
)

# Fix 4: EXPLORE phase
OLD_EXP = """case AltPhase::EXPLORE:
            if (concentration > gas_threshold && gas_hit_count_ >= 5 && use_layer_scan_) {
                alt_phase_ = AltPhase::CALIBRATE;
                startCalibration();
            } else if (concentration > gas_threshold && gas_hit_count_ >= 5 && use_esc_altitude_) {
                alt_phase_ = AltPhase::TRACK;
                esc_.reset(current_altitude_, z_min_, z_max_);
            }
            break;"""
NEW_EXP = """case AltPhase::EXPLORE:
            if (concentration > gas_threshold && gas_hit_count_ >= 5 && use_layer_scan_
                && calibration_cooldown_ <= 0.0f && calibration_count_ < max_calibrations_) {
                alt_phase_ = AltPhase::CALIBRATE;
                calibration_count_++;
                startCalibration();
            } else if (concentration > gas_threshold && gas_hit_count_ >= 5 && use_esc_altitude_) {
                alt_phase_ = AltPhase::TRACK;
                esc_.reset(current_altitude_, z_min_, z_max_);
            }
            break;"""
c = c.replace(OLD_EXP, NEW_EXP)

# Fix 5: TRACK -> EXPLORE
OLD_TRACK = """case AltPhase::TRACK:
            if (consecutive_misses_ >= consecutive_miss_threshold_) {
                GSL_INFO("OPGSL: {} misses -> EXPLORE", consecutive_misses_);
                alt_phase_ = AltPhase::EXPLORE;
            }
            break;"""
NEW_TRACK = """case AltPhase::TRACK:
            if (consecutive_misses_ >= consecutive_miss_threshold_) {
                GSL_INFO("OPGSL: {} misses -> EXPLORE (cooldown)", consecutive_misses_);
                alt_phase_ = AltPhase::EXPLORE;
                calibration_cooldown_ = calibration_cooldown_duration_;
                gas_hit_count_ = 0;
            }
            break;"""
c = c.replace(OLD_TRACK, NEW_TRACK)

# Fix 6: Convergence criterion
OLD_CONV = """float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    float dx = field.peak_x - cx, dy = field.peak_y - cy;
    float dist_to_peak = std::sqrt(dx*dx + dy*dy);
    bool near_peak = dist_to_peak < 1.0f;
    bool entropy_low = field.field_entropy < convergence_entropy_threshold_;

    if (near_peak && entropy_low) {
        stable_steps_count_++;
    } else {
        stable_steps_count_ = 0;
    }"""
NEW_CONV = """float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    float dx = field.peak_x - cx, dy = field.peak_y - cy;
    float dist_to_peak = std::sqrt(dx*dx + dy*dy);
    float z_best = getPosteriorBestZ();
    float dz = std::abs(z_best - current_altitude_);
    bool near_peak = dist_to_peak < 1.5f;
    bool entropy_low = field.field_entropy < convergence_entropy_threshold_;
    bool z_stable = dz < 1.5f;

    if (near_peak && entropy_low && z_stable) {
        stable_steps_count_++;
    } else {
        stable_steps_count_ = 0;
    }"""
c = c.replace(OLD_CONV, NEW_CONV)

# Fix 7: Step limit
c = c.replace("if (step_count_ >= 300) return GSLResult::Failure;", "if (step_count_ >= 500) return GSLResult::Failure;")

# Fix 8: Min steps
c = c.replace("if (step_count_ < 30) return GSLResult::Running;  // minimum steps before convergence", "if (step_count_ < 50) return GSLResult::Running;  // minimum steps")

# Fix 9: Min time
c = c.replace("convergence_min_time_ = 15.0f", "convergence_min_time_ = 30.0f")

# Fix 10: Comment
c = c.replace("// FIX: Use proper Bayesian update with Gaussian concentration kernel",
              "// Kernel-weighted score accumulator with temporal forgetting")

with open(CPP, "w") as f:
    f.write(c)

# Verify
with open(CPP, "r") as f:
    v = f.read()
checks = [
    ("eta = alpha_h * eta + (measurement - prev_y)", "HP filter"),
    ("field_baseline = std::exp(fld.log_field", "ESC residual"),
    ("calibration_cooldown_", "Phase hysteresis"),
    ("z_stable", "Convergence z"),
    ("step_count_ >= 500", "Step limit 500"),
    ("calibration_count_ < max_calibrations_", "Cal limit"),
    ("gas_hit_count_ = 0", "Hit reset"),
    ("std::max(0.0f, residual)", "Residual max"),
]
for needle, label in checks:
    print(f"  {'OK' if needle in v else 'MISS'} {label}")
