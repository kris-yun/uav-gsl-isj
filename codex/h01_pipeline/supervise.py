"""Orchestrate readiness and terminal flush without extending simulation time."""
import argparse,json,pathlib,re,subprocess,time
p=argparse.ArgumentParser(); p.add_argument('--run-dir',type=pathlib.Path,required=True); a=p.parse_args()
log=a.run_dir/'launch.log'; deadline=time.monotonic()+850
while time.monotonic()<deadline:
    text=log.read_text(errors='replace') if log.exists() else ''
    if 'Entering StopAndMeasure' in text: break
    time.sleep(.1)
else: raise SystemExit('PMFS_READINESS_TIMEOUT')
print('PMFS_READY_BEFORE_SIM_CLOCK_START',flush=True)
subprocess.run(['ros2','service','call','/start_simulation','std_srvs/srv/Trigger','{}'],check=True,timeout=20)
while time.monotonic()<deadline:
    text=log.read_text(errors='replace')
    match=re.search(r'RESULT IS: Success=([^,]+), Search_t=([0-9.]+), Error=([0-9.]+)',text)
    if match:
        assert 295<=float(match[2])<=330,match.group()
        (a.run_dir/'supervisor_terminal.json').write_text(json.dumps({'terminal':match.group(),'wall_time':time.time(),'scientific_budget_s':300,'status':'NATIVE_TERMINAL_RECEIVED'},indent=2)+'\n')
        # Standard case runner now performs only its documented 3+5 s flush/cleanup.
        status=a.run_dir/'run_status.json'
        if not status.exists():
            status.write_text(json.dumps({'status':'native_terminal_received','gsl_result_code':match.group(),'gsl_action_status':'native_terminal_saved'},indent=2)+'\n')
        print('NATIVE_TERMINAL_RECEIVED',flush=True)
        break
    time.sleep(.1)
else: raise SystemExit('NATIVE_TERMINAL_TIMEOUT')
