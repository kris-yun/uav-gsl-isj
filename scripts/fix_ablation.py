f = '/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_ablation.launch.py'
with open(f) as fh:
    c = fh.read()

# Disable CP and DDM
c = c.replace('DeclareLaunchArgument("opgsl_cp", default_value="true")', 'DeclareLaunchArgument("opgsl_cp", default_value="false")')
c = c.replace('DeclareLaunchArgument("opgsl_ddm", default_value="true")', 'DeclareLaunchArgument("opgsl_ddm", default_value="false")')

# Update start position and source
c = c.replace('default_value="-0.9"', 'default_value="4.0"')
c = c.replace('default_value="0.15"', 'default_value="4.0"')
c = c.replace('default_value="-0.40"', 'default_value="5.00"')
c = c.replace('default_value="-2.90"', 'default_value="6.20"')
c = c.replace('default_value="-0.30"', 'default_value="0.50"')
c = c.replace('default_value="/home/zyc/vgr_data_scenarios/House01"', 'default_value="/home/zyc/enva_vgr"')
c = c.replace('default_value="2,4-1_fast"', 'default_value="A1_fast"')

with open(f, 'w') as fh:
    fh.write(c)
print('Updated vgr_ablation.launch.py: disabled CP/DDM, updated start/source/env')
