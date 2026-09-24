#!/usr/bin/env python3
"""Audit the C0.5 spatial snapshot time contract.

The C0.5 exporter selected GADEN files by save-counter names:
  iteration_100,150,...,550
and labelled them as 50,75,...,275 s by multiplying the counter by 0.5 s.

GADEN RunningSimulation::SaveResults names files with last_saved_step, which
increments once per SAVE, while saving occurs under float32:
  currentTime > lastSaveTime + saveDeltaTime
before currentTime += dt.

Therefore iteration_N is a save counter, not a physical-time index.
"""
from __future__ import annotations
import json
import numpy as np

SELECTED=(100,150,200,250,300,350,400,450,500,550)
LEGACY_LABELS=(50,75,100,125,150,175,200,225,250,275)

def save_schedule(n_saves:int,dt:float=.1,save_dt:float=.5):
    current=np.float32(0.0)
    last=np.float32(-np.finfo(np.float32).max)
    d=np.float32(dt); sd=np.float32(save_dt)
    steps=[]; times=[]
    step=0
    while len(steps)<n_saves:
        if current > np.float32(last+sd):
            steps.append(step); times.append(float(current)); last=current
        current=np.float32(current+d)
        step+=1
    return np.asarray(steps),np.asarray(times)

def main():
    steps,times=save_schedule(max(SELECTED)+1)
    rows=[]
    for idx,label in zip(SELECTED,LEGACY_LABELS):
        # Save occurs after AddFilaments + MoveFilaments at loop currentIteration.
        model_updates=int(steps[idx])+1
        rows.append({
          "file":f"iteration_{idx}",
          "legacy_label_s":float(label),
          "save_loop_step":int(steps[idx]),
          "state_after_model_updates":model_updates,
          "gaden_current_time_s":float(times[idx]),
          "model_record_time_s":model_updates*0.1,
          "legacy_time_error_s":float(times[idx]-label),
        })
    out={
      "decision":"C0_5_SPATIAL_TIME_CONTRACT_INVALID",
      "selected_save_counters":list(SELECTED),
      "rows":rows,
      "correct_model_record_steps":[r["state_after_model_updates"] for r in rows],
      "correct_model_record_times_s":[r["model_record_time_s"] for r in rows],
    }
    print(json.dumps(out,indent=2))

if __name__=="__main__":
    main()
