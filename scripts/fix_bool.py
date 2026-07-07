f = '/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_edpa_full.launch.py'
with open(f) as fh:
    c = fh.read()

# Fix: use proper ROS2 boolean parameter passing
c = c.replace('"opgsl.modules.ddm": False,', '"opgsl.modules.ddm": _bool("use_ddm"),')
c = c.replace('"opgsl.modules.cp": False,', '"opgsl.modules.cp": _bool("use_cp"),')

# Also change the launch argument defaults
c = c.replace('DeclareLaunchArgument("use_ddm", default_value="true")', 'DeclareLaunchArgument("use_ddm", default_value="false")')
c = c.replace('DeclareLaunchArgument("use_cp", default_value="true")', 'DeclareLaunchArgument("use_cp", default_value="false")')

# Set EDPA params for practical stopping
c = c.replace('"opgsl.edpa.stop_epsilon": 3.0', '"opgsl.edpa.stop_epsilon": 2.0')
c = c.replace('"opgsl.edpa.stop_delta": 0.05', '"opgsl.edpa.stop_delta": 0.10')
c = c.replace('"opgsl.edpa.stop_eta": 2.0', '"opgsl.edpa.stop_eta": 1.0')

with open(f, 'w') as fh:
    fh.write(c)
print('Fixed boolean params and EDPA tuning')
