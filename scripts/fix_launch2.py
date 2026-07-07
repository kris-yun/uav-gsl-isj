f = '/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_edpa_full.launch.py'
with open(f) as fh:
    c = fh.read()
# Disable CP and DDM for EDPA-only stopping
c = c.replace('"opgsl.modules.ddm": _bool("use_ddm")', '"opgsl.modules.ddm": False')
c = c.replace('"opgsl.modules.cp": _bool("use_cp")', '"opgsl.modules.cp": False')
# Increase EDPA epsilon to allow stopping when close enough
c = c.replace('"opgsl.edpa.stop_epsilon": 2.0', '"opgsl.edpa.stop_epsilon": 3.0')
with open(f, 'w') as fh:
    fh.write(c)
print('Updated: CP/DDM disabled, EDPA epsilon=3.0')
