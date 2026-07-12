import subprocess, os, time
os.system("killall -9 gsl_actionserver_node vgr_sim_node gsl_benchmark_runner 2>/dev/null")
time.sleep(3)
cmd = "cd /home/zyc/gsl_ws && source install/setup.bash && timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 config_id:=2,4-1_fast algorithm:=OPGSL method:=M7_full_saisc_pf source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 start_x:=0.30 start_y:=-1.20 seed:=0 timeout_sec:=240 use_sbd:=true opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true opgsl.event_driven.enabled:=true opgsl.event_driven.eta_fixed:=-1.0 > /tmp/test_entropy.log 2>&1"
os.system(cmd)
log = open("/tmp/test_entropy.log").read()
for line in log.split("\n"):
    for tag in ["RESULT", "Found", "EP-STOP", "Error", "Traceback", "posterior_MAP"]:
        if tag in line:
            print(line[:200])
            break
os.system("killall -9 gsl_actionserver_node vgr_sim_node gsl_benchmark_runner 2>/dev/null")
