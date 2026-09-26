#!/usr/bin/env python3
import argparse, json, math
import pandas as pd
import numpy as np

def wrap(a):
    return (a + math.pi) % (2*math.pi) - math.pi

p = argparse.ArgumentParser()
p.add_argument("events")
p.add_argument("probes")
p.add_argument("output")
args = p.parse_args()

e = pd.read_csv(args.events)
w = pd.read_csv(args.probes)

required_probe = {"wind_state","x","y","z","u","v","speed","direction","source_file"}
missing = required_probe - set(w.columns)
if missing:
    raise SystemExit(f"probe columns missing: {sorted(missing)}")

rows=[]
for _, r in e.iterrows():
    # Match the exact event site, allowing tiny text/float round-off only.
    dxy = np.hypot(w["x"].astype(float)-float(r.robot_x),
                   w["y"].astype(float)-float(r.robot_y))
    cand = w[dxy <= 1e-5].copy()
    if cand.empty:
        raise SystemExit(f"no probe rows for event site {int(r.event_id)}")

    obs_speed=float(r.wind_speed)
    obs_dir=float(r.wind_direction)
    # PMFS consumes speed and direction separately, so retain both diagnostics.
    cand["angle_abs_rad"] = cand["direction"].astype(float).map(
        lambda a: abs(wrap(float(a)-obs_dir)))
    cand["speed_abs"] = (cand["speed"].astype(float)-obs_speed).abs()
    cand["speed_rel"] = cand["speed_abs"] / max(obs_speed, 1e-12)

    # Vector diagnostic only; it is not the scientific gate by itself.
    ou=obs_speed*math.cos(obs_dir)
    ov=obs_speed*math.sin(obs_dir)
    cand["vector_abs"] = np.hypot(cand["u"].astype(float)-ou,
                                  cand["v"].astype(float)-ov)
    cand["vector_rel_to_obs_speed"] = cand["vector_abs"] / max(obs_speed,1e-12)

    # Predeclared dimensionless ordering score. It is used only to order states.
    # No threshold is optimized from source truth.
    cand["match_order_score"] = np.hypot(
        cand["angle_abs_rad"].astype(float)/math.pi,
        np.log(np.maximum(cand["speed"].astype(float),1e-12)/max(obs_speed,1e-12))
    )

    cand=cand.sort_values(["match_order_score","wind_state","z"])
    best=cand.iloc[0]
    second=cand.iloc[1] if len(cand)>1 else None
    rows.append({
        "event_id":int(r.event_id),
        "steady_ns":int(r.steady_ns),
        "robot_x":float(r.robot_x),
        "robot_y":float(r.robot_y),
        "obs_speed":obs_speed,
        "obs_direction":obs_dir,
        "best_state":str(best.wind_state),
        "best_z":float(best.z),
        "best_angle_abs_rad":float(best.angle_abs_rad),
        "best_speed_rel":float(best.speed_rel),
        "best_vector_rel_to_obs_speed":float(best.vector_rel_to_obs_speed),
        "best_match_order_score":float(best.match_order_score),
        "second_match_order_score":None if second is None else float(second.match_order_score),
        "best_to_second_ratio":None if second is None or float(second.match_order_score)==0
            else float(best.match_order_score)/float(second.match_order_score),
        "best_source_file":str(best.source_file)
    })

out=pd.DataFrame(rows)
out.to_csv(args.output,index=False)

summary={
  "event_count":len(out),
  "best_angle_abs_rad_median":float(out.best_angle_abs_rad.median()),
  "best_angle_abs_rad_max":float(out.best_angle_abs_rad.max()),
  "best_speed_rel_median":float(out.best_speed_rel.median()),
  "best_speed_rel_max":float(out.best_speed_rel.max()),
  "best_vector_rel_median":float(out.best_vector_rel_to_obs_speed.median()),
  "best_vector_rel_max":float(out.best_vector_rel_to_obs_speed.max()),
  "matched_states":out.best_state.tolist(),
  "note":"Ordering diagnostics only. Final contract decision must also use adapter source semantics and documented sensor averaging/noise."
}
print(json.dumps(summary,indent=2))
