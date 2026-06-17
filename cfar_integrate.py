import os

# 1. Add CFAR settings to Settings.hpp
settings_path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/internal/Settings.hpp"
with open(settings_path, "r") as f:
    content = f.read()

# Add CFAR struct after ReviewInnovationSettings
cfar_struct = """
    struct CfarSettings {
        bool enabled{false};
        int window_size{20};
        double guard_factor{1.5};
        double min_threshold{0.001};
        double max_threshold{0.5};
    } cfar;
"""

if "cfar" not in content:
    # Insert before the closing of Settings struct
    content = content.replace("};\n\n} // namespace", cfar_struct + "};\n\n} // namespace")
    with open(settings_path, "w") as f:
        f.write(content)
    print("CFAR settings added to Settings.hpp")
else:
    print("CFAR settings already present")

# 2. Add CFAR parameter loading to PMFS.cpp
pmfs_path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp"
with open(pmfs_path, "r") as f:
    lines = f.readlines()

# Find where to add CFAR include
include_line = None
for i, line in enumerate(lines):
    if '#include' in line and 'uav_gsl_review' in line:
        include_line = i
        break

if include_line and "uav_gsl_cfar" not in "".join(lines):
    lines.insert(include_line, '#include <uav_gsl_cfar/CfarDetector.hpp>\n')
    print(f"CFAR include added at line {include_line+1}")

# Find where to add CFAR param loading (after TDC params)
tdc_logfile_line = None
for i, line in enumerate(lines):
    if 'settings.tdc.sharpen_strength' in line:
        tdc_logfile_line = i
        break

if tdc_logfile_line:
    cfar_params = """
        // CFAR: Constant False Alarm Rate adaptive threshold (radar signal processing)
        settings.cfar.enabled = getParam<bool>("cfar_enabled", false);
        settings.cfar.window_size = getParam<int>("cfar_window_size", 20);
        settings.cfar.guard_factor = getParam<double>("cfar_guard_factor", 1.5);
        settings.cfar.min_threshold = getParam<double>("cfar_min_threshold", 0.001);
        settings.cfar.max_threshold = getParam<double>("cfar_max_threshold", 0.5);
"""
    if "cfar_enabled" not in "".join(lines):
        lines.insert(tdc_logfile_line + 1, cfar_params)
        print(f"CFAR params added after line {tdc_logfile_line+1}")

with open(pmfs_path, "w") as f:
    f.writelines(lines)

# 3. Add CFAR adaptive threshold to processGasAndWindMeasurements
# Find the gas_hit line and add CFAR logic before it
with open(pmfs_path, "r") as f:
    content = f.read()

cfar_block = """            // CFAR: adaptive threshold based on local noise floor
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
            const bool gas_hit = concentration > effective_threshold;
"""

if "CFAR" not in content:
    # Replace the fixed gas_hit line
    old_gas_hit = "            const bool gas_hit = concentration > thresholdGas;"
    if old_gas_hit in content:
        content = content.replace(old_gas_hit, cfar_block)
        with open(pmfs_path, "w") as f:
            f.write(content)
        print("CFAR adaptive threshold inserted")
    else:
        print("ERROR: gas_hit line not found")
else:
    print("CFAR already integrated")

# 4. Add cfar_window_ to PMFS.hpp
hpp_path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.hpp"
with open(hpp_path, "r") as f:
    hpp_content = f.read()

if "cfar_window_" not in hpp_content:
    # Add after review_peak_history_
    hpp_content = hpp_content.replace(
        "review_peak_history_",
        "review_peak_history_;\n    std::vector<double> cfar_window_  // CFAR sliding window"
    )
    with open(hpp_path, "w") as f:
        f.write(hpp_content)
    print("cfar_window_ added to PMFS.hpp")
else:
    print("cfar_window_ already in PMFS.hpp")

# 5. Add to launch file
launch_path = "/home/zyc/ros2_ws/src/vgr_bridge/launch/vgr_gsl_unified_ablation.launch.py"
with open(launch_path, "r") as f:
    launch_content = f.read()

if "cfar_enabled" not in launch_content:
    cfar_args = '''        arg("cfar_enabled", "false"),
        arg("cfar_window_size", "20"),
        arg("cfar_guard_factor", "1.5"),
        arg("cfar_min_threshold", "0.001"),
        arg("cfar_max_threshold", "0.5"),
'''
    # Insert after eae args
    launch_content = launch_content.replace(
        'arg("eae_max_extension_factor", "2.0"),',
        'arg("eae_max_extension_factor", "2.0"),\n' + cfar_args
    )
    with open(launch_path, "w") as f:
        f.write(launch_content)
    print("CFAR args added to launch file")
else:
    print("CFAR args already in launch file")

print("CFAR_INTEGRATION_DONE")
