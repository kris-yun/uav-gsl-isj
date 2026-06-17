f = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp"
with open(f, "r") as fh:
    content = fh.read()

old = "            const bool gas_hit = concentration > thresholdGas;"
new = """            // CFAR: adaptive threshold based on local noise floor (radar signal processing)
            double effective_threshold = thresholdGas;
            if (settings.cfar.enabled) {
                cfar_window_.push_back(raw_concentration);
                if ((int)cfar_window_.size() > settings.cfar.window_size)
                    cfar_window_.erase(cfar_window_.begin());
                if (cfar_window_.size() >= 3) {
                    std::vector<double> sorted = cfar_window_;
                    std::sort(sorted.begin(), sorted.end());
                    double q25 = sorted[sorted.size() / 4];
                    effective_threshold = std::max(settings.cfar.min_threshold,
                        std::min(settings.cfar.max_threshold, q25 * settings.cfar.guard_factor));
                    if (settings.method.verbose_debug)
                        GSL_INFO("[CFAR] thresh={:.4f} noise={:.4f} window={}", effective_threshold, q25, cfar_window_.size());
                }
            }
            const bool gas_hit = concentration > effective_threshold;"""

if old in content:
    content = content.replace(old, new)
    with open(f, "w") as fh:
        fh.write(content)
    print("CFAR_THRESHOLDED")
else:
    print("OLD_NOT_FOUND")
