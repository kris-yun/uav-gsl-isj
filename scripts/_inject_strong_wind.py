with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp', 'r') as f:
    content = f.read()

# Change oracle wind to use STRONG wind
old = 'oracle_speed = getParam<double>("oracle_wind_speed", 0.088);'
new = 'oracle_speed = getParam<double>("oracle_wind_speed", 0.5);'

content = content.replace(old, new)

with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp', 'w') as f:
    f.write(content)
print('oracle wind speed changed to 0.5 m/s')
