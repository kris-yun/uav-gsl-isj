import re
f = '/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_edpa_full.launch.py'
with open(f) as fh:
    c = fh.read()
c = c.replace('"opgsl.edpa.stop_epsilon": 0.5', '"opgsl.edpa.stop_epsilon": 2.0')
c = c.replace('"opgsl.edpa.stop_delta": 0.10', '"opgsl.edpa.stop_delta": 0.05')
c = c.replace('"opgsl.edpa.stop_eta": 5.0', '"opgsl.edpa.stop_eta": 2.0')
with open(f, 'w') as fh:
    fh.write(c)
print('Updated launch file parameters')
