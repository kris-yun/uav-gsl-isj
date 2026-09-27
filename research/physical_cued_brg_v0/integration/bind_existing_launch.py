#!/usr/bin/env python3
"""Port the actual recovered Native launch with explicit parameter additions."""
import argparse,hashlib,json
from pathlib import Path
def once(s,old,new):
    if s.count(old)!=1:raise ValueError(old[:80])
    return s.replace(old,new,1)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--original',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    src=Path(a.original);p=Path(a.out);s=src.read_text()
    s=once(s,'    "shadow_gmrf": "false",','''    "shadow_gmrf": "false",
    "recorded_snapshot_time_map": "", "gaden_iteration_mode": "recorded_snapshot_time_replay",
    "brg_enabled": "false", "brg_port": "17831", "brg_candidates": "624",
    "brg_bank_sha256": "", "brg_run_id": "UNSET", "brg_sensor_offset_z_m": "0.0",
    "pmfs_belief_file": "",''')
    s=once(s,'"gaden_iteration_mode": "seeded_time_replay",','''"gaden_iteration_mode": LC("gaden_iteration_mode"),
            "recorded_snapshot_time_map": LC("recorded_snapshot_time_map"),''')
    s=once(s,'            "scale": _typed("scale", int), "seed": _typed("seed", int),','''            "scale": _typed("scale", int), "seed": _typed("seed", int),
            "use_sim_time": True,
            "brg_enabled": _typed("brg_enabled", bool), "brg_port": _typed("brg_port", int),
            "brg_candidates": _typed("brg_candidates", int), "brg_bank_sha256": LC("brg_bank_sha256"),
            "brg_run_id": LC("brg_run_id"), "brg_sensor_offset_z_m": _typed("brg_sensor_offset_z_m", float),
            "measurement_trace_file": _file("measurement_blocks.csv"),
            "continuous_measurement_samples_file": _file("measurement_samples.csv"),''')
    s=once(s,'            "algorithm": "PMFS", "method": "B4_PMFS_official",','''            "algorithm": "PMFS", "method": "B4_PMFS_official",
            "use_sim_time": True, "official_pmfs_belief_file": LC("pmfs_belief_file"),''')
    s=once(s,'''    args.append(TimerAction(period=8.0, actions=[ExecuteProcess(
        cmd=["ros2", "service", "call", "/start_simulation", "std_srvs/srv/Trigger", "{}"],
        output="screen")]))''','''    # Case adapter starts /clock after the initialized belief is recorded at t=0.
    # A fixed wall timer can consume plume/search time during DDS discovery.''')
    p.write_text(s)
    Path(str(p)+'.json').write_text(json.dumps({'actual_original_launch':str(src),'original_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
        'bound_launch':str(p),'bound_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'native_parameters_changed_by_neural_arm':False},indent=2)+'\n')
if __name__=='__main__':main()
