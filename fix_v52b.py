path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path) as f:
    code = f.read()

# Fix overshoot detection: require 3 consecutive drops, not just 1
old_overshoot = """    // -- Overshoot detection: if concentration peaked and dropped, reverse --
    bool overshoot_detected = false;
    if (obs_history_c_.size() >= 5) {
        int n = obs_history_c_.size();
        float peak_c = 0; int peak_idx = 0;
        for (int i = n-5; i < n; i++) {
            if (obs_history_c_[i] > peak_c) { peak_c = obs_history_c_[i]; peak_idx = i; }
        }
        // If peak was 2+ steps ago and current is <50% of peak -> overshoot
        if (peak_idx < n-2 && peak_c > 0.01f && latest_gas_ < peak_c * 0.5f) {
            overshoot_detected = true;
            // Navigate back toward peak position
            float px = obs_history_x_[peak_idx], py = obs_history_y_[peak_idx];
            float dx = px - cx, dy = py - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                float ret_step = std::min(1.5f, d * 0.6f);
                best_x = cx + ret_step * dx / d;
                best_y = cy + ret_step * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV: overshoot detected! returning to peak ({:.2f},{:.2f}) peak_c={:.3f}",
                         best_x, best_y, peak_c);
                return;
            }
        }
    }"""

new_overshoot = """    // -- V5.2: Overshoot detection: require 3 consecutive drops --
    bool overshoot_detected = false;
    if (obs_history_c_.size() >= 7) {
        int n = obs_history_c_.size();
        // Find peak in last 7 readings
        float peak_c = 0; int peak_idx = 0;
        for (int i = n-7; i < n; i++) {
            if (obs_history_c_[i] > peak_c) { peak_c = obs_history_c_[i]; peak_idx = i; }
        }
        // Check for 3 consecutive drops after peak
        if (peak_idx < n-3 && peak_c > 0.05f) {
            bool three_drops = true;
            for (int i = peak_idx+1; i < n && i < peak_idx+4; i++) {
                if (obs_history_c_[i] >= obs_history_c_[i-1] * 0.8f) {
                    three_drops = false;
                    break;
                }
            }
            if (three_drops && latest_gas_ < peak_c * 0.3f) {
                overshoot_detected = true;
                float px = obs_history_x_[peak_idx], py = obs_history_y_[peak_idx];
                float dx = px - cx, dy = py - cy;
                float d = std::sqrt(dx*dx + dy*dy);
                if (d > 0.5f) {
                    float ret_step = std::min(1.5f, d * 0.5f);
                    best_x = cx + ret_step * dx / d;
                    best_y = cy + ret_step * dy / d;
                    clipToMapBounds(best_x, best_y);
                    GSL_INFO("SDNBV: SUSTAINED overshoot! returning to peak ({:.2f},{:.2f}) peak_c={:.3f}",
                             best_x, best_y, peak_c);
                    return;
                }
            }
        }
    }"""

code = code.replace(old_overshoot, new_overshoot)

with open(path, 'w') as f:
    f.write(code)
print("V5.2 overshoot fix: require 3 consecutive drops + peak_c > 0.05")