#!/bin/bash
source /opt/ros/humble/setup.bash
cd /home/zyc/gsl_ws
rm -rf build/gsl_server install/gsl_server
colcon build --packages-select gsl_server