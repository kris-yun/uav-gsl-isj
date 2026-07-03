path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp"
with open(path) as f:
    content = f.read()

old = """        last_concentration = concentration;
        last_windSpeed = windSpeed;
        last_windDirection = windDirection;
        // ============================================================
        // BWE:"""

new = """        last_concentration = concentration;
        last_windSpeed = windSpeed;
        last_windDirection = windDirection;

        // WRANF mid-navigation update: accumulate gas hits during flight
        if (movingState) {
            auto* pmfs_moving = dynamic_cast<MovingStatePMFS*>(movingState.get());
            if (pmfs_moving) {
                pmfs_moving->updateWranfMidNavigation();
            }
        }

        // ============================================================
        // BWE:"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added WRANF mid-nav call")
else:
    print("ERROR: Pattern not found")
