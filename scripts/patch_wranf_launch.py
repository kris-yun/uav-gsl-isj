import re
path = "/home/zyc/ros2_ws/src/vgr_bridge/launch/vgr_gsl_wranf.launch.py"
with open(path) as f:
    content = f.read()

# Add PWC parameters after the WRANF override parameters
pwc_params = '''                # PWC: Plume Wind Correction
                "pwc_enabled": True,
                "pwc_alpha": 50.0,
                "pwc_beta": 0.5,
                "pwc_max_correction": 5.0,
                "pwc_min_wind": 0.005,
                "pwc_use_adaptive": True,
                "pwc_plume_scale_factor": 1.0,
                "pwc_log_file": "/tmp/pwc_log.csv",'''

if "pwc_enabled" not in content:
    # Insert after wranf_log_file line
    content = content.replace(
        '"wranf_log_file": "/tmp/wranf_supervisor_log.csv",',
        '"wranf_log_file": "/tmp/wranf_supervisor_log.csv",\n' + pwc_params
    )
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added PWC params to WRANF launch")
else:
    print("PWC params already present")
