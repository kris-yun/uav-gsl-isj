#!/usr/bin/env python3
script = """#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

D=/tmp/edpa_exp2
mkdir -p $D

echo "=== EDPA 10-seed batch ==="
for S in 0 1 2 3 4 5 6 7 8 9; do
  echo "Running seed $S ..."
  timeout 300 ros2 launch vgr_bridge vgr_edpa.launch.py seed:=$S resultsFile:=$D/edpa_s${S}.csv > $D/edpa_s${S}.log 2>&1
  echo "Seed $S done"
  grep map_dist $D/edpa_s${S}.csv 2>/dev/null | tail -1
  pkill -f gsl_actionserver 2>/dev/null
  pkill -f vgr_sim_node 2>/dev/null
  pkill -f gsl_benchmark 2>/dev/null
  sleep 2
done

echo "=== Results ==="
for S in 0 1 2 3 4 5 6 7 8 9; do
  echo -n "Seed $S: "
  tail -1 $D/edpa_s${S}.csv 2>/dev/null || echo "FAILED"
done
echo "=== ALL DONE ==="
"""

with open("/tmp/batch2.py", "w") as f:
    f.write("#!/usr/bin/env python3\\nimport os\\nos.system('''" + script + "''')\\n")
print("ok")
