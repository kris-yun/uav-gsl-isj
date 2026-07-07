# Update launch files
for lf, val in [
    ('/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_edpa_full.launch.py', 'True'),
    ('/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_baseline_full.launch.py', 'False'),
]:
    with open(lf) as f:
        c = f.read()
    if 'opgsl.modules.event_driven' not in c:
        # Add after opgsl.modules.edpa line
        c = c.replace(
            '"opgsl.edpa.detection_threshold": 0.01,',
            '"opgsl.edpa.detection_threshold": 0.01,\n                "opgsl.modules.event_driven": ' + val + ','
        )
        with open(lf, 'w') as f:
            f.write(c)
        print(f'Updated {lf} with event_driven={val}')
    else:
        print(f'{lf} already has event_driven')
