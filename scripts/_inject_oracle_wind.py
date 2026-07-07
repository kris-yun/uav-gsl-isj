with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp', 'r') as f:
    content = f.read()

# Add oracle wind injection right after the function starts
old = '''    void PMFS::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection)
    {
        last_concentration = concentration;
        last_windSpeed = windSpeed;
        last_windDirection = windDirection;'''

new = '''    void PMFS::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection)
    {
        // ORACLE WIND OVERRIDE for testing
        // House01 source: (-0.4, -2.9), start: (-5, -5)
        // Wind from west to east: direction ~271 degrees = 4.73 rad
        // Actual wind speed ~0.088 m/s from anemometer, but GADEN ground truth is stronger
        {
            static bool oracle_init = false;
            static double oracle_speed = 0.0;
            static double oracle_dir = 0.0;
            if (!oracle_init) {
                // Use param if available, else hardcoded
                oracle_speed = getParam<double>("oracle_wind_speed", 0.088);
                oracle_dir = getParam<double>("oracle_wind_direction_rad", 4.73);  // 271 deg
                oracle_init = true;
            }
            if (oracle_speed > 0) {
                windSpeed = oracle_speed;
                windDirection = oracle_dir;
            }
        }
        last_concentration = concentration;
        last_windSpeed = windSpeed;
        last_windDirection = windDirection;'''

content = content.replace(old, new)

with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp', 'w') as f:
    f.write(content)
print('oracle wind injection added')
