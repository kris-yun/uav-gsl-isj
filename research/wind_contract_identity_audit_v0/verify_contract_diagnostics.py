#!/usr/bin/env python3
"""Read-only checks of recorded wind semantics, not a localization experiment."""
import csv, json, math
from pathlib import Path
import numpy as np
import pandas as pd

root=Path('/home/zyc/wind_contract_identity_audit_20260926/evidence')
csvp=pd.read_csv(root/'wind_state_probe.csv')
binary=pd.read_csv(root/'binary_sensor_contract_probe.csv')
key=lambda r:(int(r.wind_state),float(r.x),float(r.y))
br={key(r):r for r in binary.itertuples()}
diff=[]
for r in csvp.itertuples():
    b=br[key(r)]
    diff.append(max(abs(float(np.float32(r.u))-b.u),abs(float(np.float32(r.v))-b.v)))
assert max(diff)<1e-15
trace=pd.read_csv(root/'assets/wind_trace.csv')
sites=csvp[['x','y']].drop_duplicates().to_numpy()
assignments=[]; site_samples={}
for si,(x,y) in enumerate(sites):
    w=binary[(abs(binary.x-x)<1e-5)&(abs(binary.y-y)<1e-5)]
    t=trace[(abs(trace.x-x)<1e-4)&(abs(trace.y-y)<1e-4)]
    site_samples[si]=[]
    for row in t.itertuples():
        err=np.hypot(w.u-float(row.wind_u),w.v-float(row.wind_v))
        j=int(np.argmin(err.to_numpy())); state=w.iloc[j]
        record={'site':'ABCD'[si],'step':int(row.step),'t_sim_s':float(row.t_sim_s),
                'iteration':int(row.iteration),'matched_file_id':int(state.wind_state),
                'vector_abs_error_from_six_decimal_trace':float(err.iloc[j]),
                'exact_u':float(state.u),'exact_v':float(state.v)}
        assignments.append(record); site_samples[si].append(record)
with (root/'trace_state_diagnostic.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(assignments[0])); writer.writeheader();writer.writerows(assignments)

# Documented ten-reading block means are checked against consecutive trace
# windows. This provides diagnostics only: ROS receipt boundaries were not
# logged, so no window is claimed as the unique actual measurement block.
events=pd.read_csv(root.parent/'code/event_vectors.csv')
windows=[]
for ei,event in enumerate(events.itertuples()):
    si=next(i for i,(x,y) in enumerate(sites) if math.hypot(x-event.robot_x,y-event.robot_y)<1e-5)
    samples=site_samples[si]; options=[]
    for begin in range(len(samples)-9):
        block=samples[begin:begin+10]
        if block[-1]['step']-block[0]['step']!=9: continue
        speeds=[]; angles=[]
        for r in block:
            speeds.append(math.hypot(r['exact_u'],r['exact_v']))
            # Anemometer direction becomes float in Algorithm::windCallback.
            angles.append(float(np.float32(math.atan2(r['exact_v'],r['exact_u']))))
        speed_sum=np.float32(0); cx=np.float32(0); cy=np.float32(0)
        for speed,angle in zip(speeds,angles):
            speed_sum=np.float32(float(speed_sum)+speed)
            cx=np.float32(float(cx)+math.cos(angle)); cy=np.float32(float(cy)+math.sin(angle))
        avg_speed=float(np.float32(speed_sum/np.float32(10)))
        avg_angle=float(np.float32(math.atan2(float(cy),float(cx))))
        da=abs((avg_angle-event.wind_direction+math.pi)%(2*math.pi)-math.pi)
        ds=abs(avg_speed-event.wind_speed)
        order=math.hypot(da/math.pi,math.log(max(avg_speed,1e-12)/event.wind_speed))
        options.append((order,begin,da,ds,avg_speed,avg_angle))
    options.sort()
    best=options[0]; block=samples[best[1]:best[1]+10]
    windows.append({'event_id':int(event.event_id),'site':'ABCD'[si],
                    'closest_window_begin_step':block[0]['step'],'closest_window_end_step':block[-1]['step'],
                    'angle_abs_rad':best[2],'speed_abs':best[3],
                    'state_file_ids_in_closest_window':[r['matched_file_id'] for r in block],
                    'unique_actual_receipt_window_proven':False})
(root/'BLOCK_AVERAGING_DIAGNOSTIC.json').write_text(json.dumps(windows,indent=2,sort_keys=True)+'\n')
matched=pd.read_csv(root/'event_state_match.csv')
summary={
    'csv_binary_four_site_all_11_state_float32_component_max_abs_diff':max(diff),
    'csv_binary_comparison_count':len(diff),
    'same_numbered_wind_family_at_audited_sensor_sites':True,
    'sensor_z':0.3,'forward_query_z':0.0,
    'matched_state_sequence_from_supplied_analyzer':matched.best_state.astype(int).tolist(),
    'matched_sequence_is_unique_documented_state_sequence':False,
    'sensor_rule':'seeded_time_replay selects gas frame; stored frame windIndex selects lexically ordered binary wind array',
    'forward_rule':'always min CSV numeric id = 0, independent of time',
    'trace_rows_at_four_sites':len(assignments),
    'trace_nearest_binary_vector_abs_max':max(r['vector_abs_error_from_six_decimal_trace'] for r in assignments),
    'block_averaging_best_window_angle_max':max(r['angle_abs_rad'] for r in windows),
    'block_averaging_best_window_speed_abs_max':max(r['speed_abs'] for r in windows),
    'receipt_window_boundaries_available':False,
    'per_site':[]}
for i,(x,y) in enumerate(sites):
    m=matched[(abs(matched.robot_x-x)<1e-5)&(abs(matched.robot_y-y)<1e-5)]
    summary['per_site'].append({'site':'ABCD'[i],'event_count':len(m),
       'angle_abs_rad_median':float(m.best_angle_abs_rad.median()),'angle_abs_rad_max':float(m.best_angle_abs_rad.max()),
       'speed_relative_error_median':float(m.best_speed_rel.median()),'speed_relative_error_max':float(m.best_speed_rel.max()),
       'best_to_second_ratio_median':float(m.best_to_second_ratio.median()),
       'matched_states':m.best_state.astype(int).tolist()})
(root/'CONTRACT_DIAGNOSTICS.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2))
