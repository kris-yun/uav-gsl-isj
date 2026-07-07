with open('/home/zyc/ros2_ws/src/vgr_bridge/launch/vgr_gsl_rwgf.launch.py', 'r') as f:
    content = f.read()

# Adjust RWGF parameters for near-zero wind conditions
replacements = {
    '"rwgf_cone_base_angle": 30.0': '"rwgf_cone_base_angle": 15.0',
    '"rwgf_cone_max_angle": 160.0': '"rwgf_cone_max_angle": 90.0',
    '"rwgf_hit_boost": 0.15': '"rwgf_hit_boost": 0.5',
    '"rwgf_miss_decay": 0.995': '"rwgf_miss_decay": 0.99',
    '"rwgf_nav_threshold": 0.3': '"rwgf_nav_threshold": 0.001',
    '"rwgf_nav_step_size": 2.0': '"rwgf_nav_step_size": 1.5',
    '"rwgf_blur_sigma": 1.0': '"rwgf_blur_sigma": 0.5',
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('/home/zyc/ros2_ws/src/vgr_bridge/launch/vgr_gsl_rwgf.launch.py', 'w') as f:
    f.write(content)
print('params updated')
