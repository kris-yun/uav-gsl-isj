content = open("/home/zyc/gsl_ws/src/vgr_bridge/launch/vgr_ablation.launch.py").read()
# Add DeclareLaunchArgument for max_steps
old = 'DeclareLaunchArgument("opgsl_cp", default_value="true"),'
new = 'DeclareLaunchArgument("opgsl_cp", default_value="true"),\n        DeclareLaunchArgument("opgsl_max_steps", default_value="-1"),'
content = content.replace(old, new)
# Add to parameters dict
old2 = '"opgsl.event_driven.alpha_w": 0.5,'
new2 = '"opgsl.event_driven.alpha_w": 0.5,\n                "opgsl.max_steps": _int("opgsl_max_steps"),'
content = content.replace(old2, new2)
open("/home/zyc/gsl_ws/src/vgr_bridge/launch/vgr_ablation.launch.py", "w").write(content)
print("Patched launch file")
