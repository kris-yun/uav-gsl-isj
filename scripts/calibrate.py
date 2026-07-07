# Fix launch files with calibrated parameters
# Key insight: lambda0 too low, needs to be higher for strong detections near source
# Also increase ell (characteristic length) for better far-field sensitivity

for lf in [
    '/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_edpa_full.launch.py',
]:
    with open(lf) as f:
        c = f.read()
    
    # Add calibrated event-driven parameters
    old = '"opgsl.edpa.detection_threshold": 0.01,'
    new = '''"opgsl.edpa.detection_threshold": 0.01,
                "opgsl.edpa.lambda0": 5.0,
                "opgsl.edpa.ell": 4.0,
                "opgsl.edpa.alphaw": 0.3,'''
    c = c.replace(old, new)
    
    with open(lf, 'w') as f:
        f.write(c)
    print(f'Updated {lf}')

# Also need to update the code to use these parameters from launch file
# Currently hardcoded in the update function
print('NOTE: lambda0/ell/alphaw are hardcoded in OPGSL.cpp update function')
print('Need to pass them from the OPGSL member variables')
