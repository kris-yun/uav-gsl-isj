f = '/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_edpa_full.launch.py'
with open(f) as fh:
    c = fh.read()
# Keep EDPA enabled for monitoring but set epsilon very low to prevent stopping
c = c.replace('"opgsl.edpa.stop_epsilon": 2.0', '"opgsl.edpa.stop_epsilon": 0.1')
with open(f, 'w') as fh:
    fh.write(c)

f2 = '/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_baseline_full.launch.py'
with open(f2) as fh:
    c2 = fh.read()
# Disable CP and DDM in baseline too
c2 = c2.replace('"opgsl.modules.ddm": True,', '"opgsl.modules.ddm": False,')
c2 = c2.replace('"opgsl.modules.cp": True,', '"opgsl.modules.cp": False,')
with open(f2, 'w') as fh:
    fh.write(c2)

print('Fixed: EDPA epsilon=0.1 (monitor only), baseline CP/DDM disabled')
