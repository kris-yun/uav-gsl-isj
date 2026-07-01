# Fix WR-SFE for low wind: add max-concentration fallback
import sys
sys.stdout.reconfigure(encoding="utf-8")

HPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/WATS_GSL.hpp"
with open(HPP, "r") as f:
    lines = f.readlines()

# Find the FieldEstimate struct and add max_conc tracking
for i, line in enumerate(lines):
    if "float field_entropy;" in line:
        # Add max concentration tracker after field_entropy
        insert = """        float max_conc_x = 0.0f, max_conc_y = 0.0f;  // Max concentration position
        float max_conc_val = 0.0f;                   // Max concentration value
        float mean_wind_speed = 0.0f;                // Mean wind speed for fallback threshold
"""
        lines.insert(i + 1, insert)
        print(f"HPP: Added max_conc tracking after line {i+1}")
        break

# Find addObservation to track max concentration position
for i, line in enumerate(lines):
    if "observations_.push_back(obs);" in line or "observations_.emplace_back" in line:
        # Add max conc tracking before the push_back
        insert = """        // Track max concentration position for low-wind fallback
        if (obs.gas_reading > field_estimate_.max_conc_val) {
            field_estimate_.max_conc_val = obs.gas_reading;
            field_estimate_.max_conc_x = obs.x;
            field_estimate_.max_conc_y = obs.y;
        }
        // Update mean wind speed
        float ws = std::sqrt(obs.wind_x * obs.wind_x + obs.wind_y * obs.wind_y);
        field_estimate_.mean_wind_speed = 0.9f * field_estimate_.mean_wind_speed + 0.1f * ws;
"""
        lines.insert(i, insert)
        print(f"HPP: Added max_conc tracking before line {i+1}")
        break

with open(HPP, "w") as f:
    f.writelines(lines)

# Now find computeField() and add low-wind fallback for peak
with open(HPP, "r") as f:
    content = f.read()

# Find where peak_x/peak_y are set
old_peak = """        field_estimate_.peak_x = peak_i * res - half;
        field_estimate_.peak_y = peak_j * res - half;"""

new_peak = """        field_estimate_.peak_x = peak_i * res - half;
        field_estimate_.peak_y = peak_j * res - half;

        // LOW-WIND FALLBACK: when wind is very low, WR-SFE kernel shift is negligible
        // and field peak is unreliable. Fall back to max-concentration position.
        float WIND_THRESHOLD = 0.2f;  // m/s
        if (field_estimate_.mean_wind_speed < WIND_THRESHOLD && field_estimate_.max_conc_val > 0.01f) {
            // Blend: mostly max-conc position when wind is very low
            float alpha = field_estimate_.mean_wind_speed / WIND_THRESHOLD;  // 0 at zero wind, 1 at threshold
            alpha = std::clamp(alpha, 0.0f, 1.0f);
            field_estimate_.peak_x = alpha * field_estimate_.peak_x + (1.0f - alpha) * field_estimate_.max_conc_x;
            field_estimate_.peak_y = alpha * field_estimate_.peak_y + (1.0f - alpha) * field_estimate_.max_conc_y;
        }"""

if old_peak in content:
    content = content.replace(old_peak, new_peak)
    print("HPP: Added low-wind fallback for peak")
else:
    print("WARN: Could not find peak assignment")

# Also need to reset max_conc in init/reset
content = content.replace(
    "field_estimate_.visit_density.setZero();",
    "field_estimate_.visit_density.setZero();\n        field_estimate_.max_conc_val = 0.0f;\n        field_estimate_.max_conc_x = 0.0f;\n        field_estimate_.max_conc_y = 0.0f;"
)
print("HPP: Added max_conc reset")

with open(HPP, "w") as f:
    f.write(content)
print("Done!")
