"""Add WRANF mid-navigation update to processGasAndWindMeasurements"""
import re

# Read PMFS.cpp
pmfs_path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp"
with open(pmfs_path) as f:
    content = f.read()

# Add WRANF mid-nav update after storing sensor readings
# Find the pattern where last_concentration is stored
old_storage = """        // Store for WRANF supervisor input
        last_concentration = concentration;
        last_windSpeed = windSpeed;
        last_windDirection = windDirection;

        static int number_of_updates = 0;"""

new_storage = """        // Store for WRANF supervisor input
        last_concentration = concentration;
        last_windSpeed = windSpeed;
        last_windDirection = windDirection;

        // WRANF mid-navigation update: run supervisor on every sensor callback
        // This allows WRANF to accumulate gas hits and trigger goal overrides during flight
        if (movingState) {
            auto* pmfs_moving = dynamic_cast<MovingStatePMFS*>(movingState.get());
            if (pmfs_moving) {
                pmfs_moving->updateWranfMidNavigation();
            }
        }

        static int number_of_updates = 0;"""

if old_storage in content:
    content = content.replace(old_storage, new_storage)
    with open(pmfs_path, 'w') as f:
        f.write(content)
    print("OK: Added WRANF mid-nav update to PMFS.cpp")
else:
    print("ERROR: Pattern not found in PMFS.cpp")
    # Check if the storage block exists
    if "last_concentration" in content:
        print("  last_concentration exists but pattern differs")
    else:
        print("  last_concentration NOT found")

# Now add updateWranfMidNavigation to MovingStatePMFS.hpp
hpp_path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.hpp"
with open(hpp_path) as f:
    hpp = f.read()

if "updateWranfMidNavigation" not in hpp:
    # Add public method
    hpp = hpp.replace(
        '        void publishMarkers();',
        '''        void publishMarkers();
        void updateWranfMidNavigation();  // WRANF: run supervisor during navigation'''
    )
    with open(hpp_path, 'w') as f:
        f.write(hpp)
    print("OK: Added updateWranfMidNavigation to header")
else:
    print("OK: updateWranfMidNavigation already in header")

# Now add the implementation to MovingStatePMFS.cpp
cpp_path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp"
with open(cpp_path) as f:
    cpp = f.read()

# Add the method before the closing namespace brace
implementation = """
    void MovingStatePMFS::updateWranfMidNavigation()
    {
        if (!wranfSupervisor_ || !wranfSupervisor_->config().enabled) return;
        if (!pmfs) return;

        uav_gsl_wranf::Input win;
        win.step = pmfs->iterationsCounter;
        win.time_sec = pmfs->node->now().seconds();
        win.pose_x = pmfs->currentRobotPose.pose.pose.position.x;
        win.pose_y = pmfs->currentRobotPose.pose.pose.position.y;
        win.pose_z = pmfs->currentRobotPose.pose.pose.position.z;
        win.backend_target_x = 0;  // not relevant for mid-nav
        win.backend_target_y = 0;
        win.backend_target_z = 0;
        win.gas_concentration = pmfs->last_concentration;
        win.wind_x = pmfs->last_windSpeed * std::cos(pmfs->last_windDirection);
        win.wind_y = pmfs->last_windSpeed * std::sin(pmfs->last_windDirection);
        win.server_variance = 0.0;
        win.server_iterations = pmfs->iterationsCounter;

        // Just update internal state (SENPAI window, GRACE memory)
        // Goal override will happen at next chooseGoalAndMove call
        wranfSupervisor_->update(win);
    }

"""

# Find the end of the namespace
if "updateWranfMidNavigation" not in cpp:
    # Insert before the last closing brace
    last_brace = cpp.rfind("}")
    cpp = cpp[:last_brace] + implementation + cpp[last_brace:]
    with open(cpp_path, 'w') as f:
        f.write(cpp)
    print("OK: Added updateWranfMidNavigation implementation")
else:
    print("OK: updateWranfMidNavigation already implemented")
