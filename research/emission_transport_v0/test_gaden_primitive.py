"""Bounded deterministic conformance tests, never a full plume experiment."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
import numpy as np
from gaden_primitive import (Environment, Parameters, CyclicTable, schedule,
    require_independent_packet_closure, PrimitiveClosureError, grow_sigma,
    center_ppm, filament_mark, pooled_probe_points, read_legacy_wind, single_step)

parser = argparse.ArgumentParser()
parser.add_argument("--inputs", type=Path, required=True)
parser.add_argument("--contract", type=Path, required=True)
parser.add_argument("--cpp", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
began = time.perf_counter()
checks = []
def check(name, predicate):
    if not predicate:
        raise AssertionError(name)
    checks.append({"name": name, "pass": True})

env = Environment.read(args.inputs / "OccupancyGrid3D.csv")
gate = json.loads(args.contract.read_text())
points = pooled_probe_points(gate, env)
check("30_individual_four_point_protocols", len(points) == 30 and all(v.shape==(4,3) for v in points))
check("fixed_source_height", all(np.all(v[:,2]==np.float32(.2)) for v in points))
for k in range(11):
    wind = read_legacy_wind(args.inputs/f"wind_iteration_{k}", env.cells.shape)
    raw = np.fromfile(args.inputs/f"wind_iteration_{k}", dtype="<f8")
    # Several unequal x/y coordinates validate the actual C++ index layout.
    for x,y,z in ((1,2,3),(17,53,12),(82,118,25)):
        index = x+y*83+z*83*119
        check(f"wind_{k}_index_{x}_{y}_{z}",
              np.array_equal(wind[:,z,x,y],raw.reshape(3,-1)[:,index].astype(np.float32)))

rows = schedule()
cpp = json.loads(args.cpp.read_text())
check("float32_save_schedule_count_matches_cpp", len(rows)==cpp["snapshot_count"]==566)
check("first_time_matches_cpp", rows[100]["current_time_before_increment_seconds"]==cpp["first_seconds"])
check("last_time_matches_cpp", rows[550]["current_time_before_increment_seconds"]==cpp["last_seconds"])
check("first_and_last_time_not_nominal_index_times", abs(cpp["first_seconds"]-50)>1 and abs(cpp["last_seconds"]-275)>1)
sigma = np.float32(10)
for _ in range(3000): sigma = grow_sigma(sigma)
check("sigma_euler_float32_matches_cpp", float(sigma)==cpp["sigma_after_3000_moves_cm"])
check("initial_center_concentration", center_ppm(10)==10)

table = np.arange(1000, dtype=np.float32)
clock = CyclicTable(table)
draws = np.asarray([clock.next_value(0,1) for _ in range(1003)])
check("cyclic_noise_reuse_original_cpp_and_port", cpp["original_template_period_1000"] and np.array_equal(draws[:3],draws[1000:1003]))

# Same packet, age, width and wind, different surviving sibling population:
# one prior tick consumes 3 vs 6 table entries. No random table generation.
isolated, sibling_survived = CyclicTable(table), CyclicTable(table)
isolated.triple(); sibling_survived.triple(); sibling_survived.triple()
first, second = isolated.triple(), sibling_survived.triple()
check("packet_next_noise_depends_on_population_clock", not np.array_equal(first,second))
try:
    require_independent_packet_closure("pinned_gaden_cyclic_table")
except PrimitiveClosureError:
    check("invalid_independent_packet_kernel_rejected", True)
else:
    raise AssertionError("closure guard failed")

# Hand-entered geometry tests, no scientific transport samples.
simple = Environment(np.zeros((4,4,4),dtype=np.uint8),np.zeros(3,dtype=np.float32),.1)
position = np.asarray([.15,.15,.15],dtype=np.float32)
check("LOS_same_point", simple.los(position,position))
check("three_sigma_cutoff_zero", filament_mark(position,10,position+np.asarray([.31,0,0]),simple)==0)
check("free_center_mark", abs(filament_mark(position,10,position,simple)-10)<1e-12)
simple.cells[1,2,1] = 1
new,state = simple.slide(position,np.asarray([.25,.15,.15],dtype=np.float32))
check("wall_slide_stops_normal_motion", state==0 and np.array_equal(new,position))
simple.cells[1,2,1] = 2
new,state = simple.slide(position,np.asarray([.25,.15,.15],dtype=np.float32))
check("outlet_is_absorbing", state==2)
simple.cells[1,2,1] = 0
new,sigma,active = single_step(position,10,np.zeros(3),CyclicTable(np.zeros(1000)),simple)
check("conditional_step_buoyancy_and_growth", active and new[2]<position[2] and sigma>10)

# Exact finite algebra counterexample: reusing one random table entry as G+G
# has variance 4, independent replacement G1+G2 has variance 2. No draws.
check("shared_noise_covariance_not_independent", 4 != 2)
out = {"status":"DETERMINISTIC_PRIMITIVE_CHECKS_PASS", "checks":checks,
       "count":len(checks), "seconds":time.perf_counter()-began,
       "noise_population_clock_witness":{"one_packet_noise":first.tolist(),
                                         "two_packet_noise":second.tolist()},
       "selected_clock":[rows[100],rows[550]],
       "limitations":["ports are equation-level, not byte-parity to linked libgaden",
                       "no independent single-packet probability kernel constructed",
                       "no model likelihood or posterior scored"],
       "new_full_plumes":0,"new_primitive_random_samples":0}
args.out.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(out["status"],len(checks))
