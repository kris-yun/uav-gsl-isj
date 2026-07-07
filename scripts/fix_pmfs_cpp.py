path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp"
with open(path) as f:
    content = f.read()

# Add storage at the beginning of processGasAndWindMeasurements
old = """    void PMFS::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection)
    {
        static int number_of_updates = 0;"""

new = """    void PMFS::processGasAndWindMeasurements(double concentration, double windSpeed, double windDirection)
    {
        // Store for WRANF supervisor input
        last_concentration = concentration;
        last_windSpeed = windSpeed;
        last_windDirection = windDirection;

        static int number_of_updates = 0;"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added sensor storage")
else:
    print("ERROR: Pattern not found")
