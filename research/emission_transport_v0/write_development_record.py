"""Write the numerical contract and one blocked decision WITHOUT scoring.

This runner intentionally does not open the concentration tensor. Hashing the
OPEN bank binds the intended assessment; no reference/target values influence
the decision or numerical choices.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np
from gaden_primitive import (Environment, pooled_probe_points, schedule,
                            require_independent_packet_closure, PrimitiveClosureError)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""): h.update(chunk)
    return h.hexdigest()

def record(path):
    return {"path":str(path),"bytes":path.stat().st_size,"sha256":sha(path)}

def write(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+"\n",encoding="utf-8")

p=argparse.ArgumentParser()
p.add_argument("--root",type=Path,required=True)
p.add_argument("--assets",type=Path,required=True)
a=p.parse_args()
started=time.perf_counter()
e=a.root/"evidence/emission_transport_v0"
inputs=e/"open_inputs"
code=a.root/"research/emission_transport_v0"
checks=json.loads((e/"PRIMITIVE_CHECKS.json").read_text())
assert checks["status"]=="DETERMINISTIC_PRIMITIVE_CHECKS_PASS"
gate=json.loads((a.assets/"gate1a_contract.json").read_text())
panel=list(csv.DictReader((a.assets/"central_panel.tsv").open(),delimiter="\t"))
assert len(panel)==168 and len({v["source_id"] for v in panel})==168
for name,expected in {
    "central_panel.tsv":"5df11712dd0e7dbef6e454c8d146427407644b9f27245c447479185ab2129d8e",
    "gate1a_contract.json":"68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334",
    "central_bank.npy":"b21a089cb015ace71a448db58bd7a2f1fee25e9a8431cbb56728f48ca39573d9",
}.items():
    assert sha(a.assets/name)==expected,(name,"SHA_DRIFT")
env=Environment.read(inputs/"OccupancyGrid3D.csv")
assert sha(inputs/"OccupancyGrid3D.csv")=="9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
points=pooled_probe_points(gate,env)
rows=schedule()
source= e/"fixed_source/src/GADEN"
fixed={str(f.relative_to(source)):record(f) for f in sorted(source.rglob("*")) if f.is_file()}
needed=["single_packet_population_independent_transition_kernel",
        "shared_noise_table_distribution_and_thread_call_assignment",
        "joint_law_approximation_error_or_exact_shared_state_solver",
        "primitive_concentration_quantization_and_accumulation_bound",
        "probability_boundary_mass_error_and_likelihood_odds_precision",
        "same_precision_per_source_forward_baseline",
        "oracle_reference_only_density_selection_grid"]
contract={
 "status":"NUMERICAL_CONTRACT_BLOCKED_BEFORE_SCORING",
 "task":"all-source stochastic release-transport distribution development",
 "scope":{"house":"House02","wind":"3,5-1_slow","sources":168,"realizations":16,
          "protocols":30,"observations_per_protocol":2,"new_full_plumes":0,
          "new_primitive_random_samples":0,"sealed_assets_read":False,
          "target_values_read_or_scored":False},
 "primitive":{"binary_sha256":"4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1",
              "libgaden_sha256":"aca55af4e39831f97c1480bb31c014eb06294ced8a71329c3aa216e6cf7991a8",
              "source_files":fixed,
              "noise":{"law":"seeded per-thread cyclic precomputed Gaussian table",
                       "table_entries":1000,"calls_per_moving_packet":3,
                       "thread_seed_includes_thread_id":False,
                       "caller_coupling":"shared cursor depends on surviving filament population and OpenMP assignment",
                       "packet_independence_certificate":None},
              "position_precision":"float32","wind_precision":"legacy float64 payload converted to float32",
              "legacy_wind_index":"x+y*nx+z*nx*ny; three consecutive component arrays",
              "noise_displacement_scale_m":.01,
              "cell_index_conversion":"glm ivec3 truncation towards zero",
              "boundary":"recursive obstacle/OOB sliding; outlet kills packet",
              "buoyancy":"sigma-dependent center ppm, butane specific gravity 2.0061",
              "width":"sigma+=15/(2*sigma)*0.1; cm",
              "temperature_wrapper_parameter_key":"wind_time_step (effective 1.0); not silently repaired",
              "parameters_concentration_kernel":"center ppm times exp(-distance_cm^2/(2*sigma_cm^2)), strict 3sigma spherical cutoff and LOS",
              "ports_bitwise_library_parity":False},
 "release":{"type":"deterministic_float32_accumulator","per_second":7,"point_source":True,
            "variable_rate_ros_argument":"not consumed by this wrapper",
            "count_by_first_last_snapshot":[rows[100]["births_total"],rows[550]["births_total"]]},
 "source_contract":record(a.assets/"central_panel.tsv"),
 "bank_contract":record(a.assets/"central_bank.npy"),
 "bank_manifest":record(a.assets/"central_manifest.tsv"),
 "observation_contract":record(a.assets/"gate1a_contract.json"),
 "time":{"snapshot_indices":[100,550],"selected": [rows[100],rows[550]],
         "basis":"reconstructed pinned float32 save loop, independently checked by C++",
         "seconds_stored_in_cube_metadata":False,
         "snapshot_files_still_available":"original runner removes realization/ after cube extraction"},
 "probes":{"type":"mean of four native cell-center samples, z=.20, same probe at two snapshots",
           "points_xyz_m":[v.tolist() for v in points],"count":30},
 "occupancy":record(inputs/"OccupancyGrid3D.csv"),
 "wind_files":[record(inputs/f"wind_iteration_{k}") for k in range(11)],
 "grid":{"native_cell_m":.1,"dimensions_xyz":[83,119,26],"native_cells":int(env.cells.size),
         "solver_state_includes":"packet age/sigma/position plus coupled noise clock; independent closure unresolved"},
 "time_step_seconds":.1,
 "likelihood":{"channel":"noiseless fixed concentration bins required; not yet instantiated",
               "ppm_bin_width":None,"accumulation_error_bound_ppm":None,
               "boundary_probability_mass_error":None,"probability_error_bound":None,
               "posterior_odds_error_bound":None,"probability_floor":None,"added_sensor_noise":None},
 "prior":{"type":"uniform","count":168,"probability":1/168},
 "hardware_budget":{"vm_ram_bytes":6163947520,"solver_max_ram_bytes":4*1024**3,
                    "solver_precompute_walltime_budget_seconds":3600,
                    "table_terms_per_law_cap":50000,
                    "policy":"budget is a cap, not evidence of achievable accuracy"},
 "baseline_contract":{"exact_moment_gaussian":"must use the same legal primitive and full covariance",
                      "per_source_forward":"same law/odds error tolerance; unresolved",
                      "robust_density_oracle":"existing 4 folds, 12 reference/4 development test; selection within reference only",
                      "selection_grid":None,"models":["Gaussian","Student-t","2D KDE"]},
 "development_retention_thresholds":{"mean_truth_log2_gain_bits_min":.05,
      "source_cluster_95pct_interval_lower_bound_min_exclusive":0,
      "mean_brier_must_not_worsen":True,"full_and_tail_trimmed_gain_must_agree":True,
      "resource_advantage_at_matched_accuracy_required":True},
 "unresolved_required_fields":needed,
 "scientific_decision":None,
}
# Contract is written before any attempt to call the composition interface.
write(e/"NUMERICAL_CONTRACT.json",contract)
try:
    require_independent_packet_closure("pinned_gaden_cyclic_table")
except PrimitiveClosureError as error:
    reason=str(error)
else:
    raise RuntimeError("Unexpected closure acceptance: refusing uncontracted scoring")
decision={"DEVELOPMENT_DECISION":"DEVELOPMENT_IMPLEMENTATION_BLOCKED_PRIMITIVE_CLOSURE",
    "scientific_decision":None,"valid_model_likelihood_constructed":False,
    "bank_scoring_started":False,"posterior_rows_generated":0,
    "mean_log2_gain_bits":None,"source_cluster_95pct_interval":None,"brier_difference":None,
    "matched_accuracy_cost_advantage":None,
    "reason":reason,
    "blocker":"The supplied product of independent packet response laws does not close the pinned simulator's shared population-dependent RNG clock.",
    "not_claimed":"This does not prove that all joint-state or controlled-approximation solvers are impossible, or that the scientific candidate failed.",
    "completed":{"upstream_math_tests":17,"deterministic_primitive_checks":checks["count"],
                 "code":"conditional single-step/LOS/wall/outlet/growth/mark/release/time/wind-layout adapter",
                 "all_source_probability_solver":"upstream finite-state solver retained; not connected to a valid GADEN stochastic kernel"},
    "actions_not_taken":["replace cyclic table with IID normal draws","fit a transport law from 168-source target bank",
                         "generate primitive Monte Carlo draws","generate full plumes","evaluate robust oracle alone as method evidence",
                         "score NLL/Brier with fabricated precision or sensor-noise floor"],
    "stop":True}
write(e/"DEVELOPMENT_DECISION.json",decision)
write(e/"COST_REPORT.json",{
    "scope":"executed deterministic checks and static storage arithmetic, not localization costs",
    "primitive_checks_wall_seconds":checks["seconds"],
    "contract_runner_wall_seconds":time.perf_counter()-started,
    "upstream_dense_transition_one_timestep_bytes":int(env.cells.size)**2*8,
    "dense_transition_all_2924_steps_bytes":int(env.cells.size)**2*8*rows[550]["moves_completed"],
    "dense_state_expansion":"illustrates why upstream toy dense storage cannot be allocated for this grid; not a lower bound on all sparse solvers",
    "precomputation_at_matched_likelihood_accuracy_seconds":None,
    "online_inference_seconds":None,"baseline_at_matched_accuracy_seconds":None,
    "max_rss_at_matched_accuracy_bytes":None,"reason_no_cost_curve":"No legal probability kernel; no matched-accuracy methods run",
    "runtime":{"python":sys.version,"numpy":np.__version__,"platform":platform.platform()}})
write(e/"POSTERIOR_OUTPUT_STATUS.json",{
    "required_rows":168*16*30,"required_columns":"168-source posterior for each of 4 methods/protocol",
    "written_rows":0,"status":"NOT_COMPUTED_IMPLEMENTATION_BLOCKED",
    "cluster_statistics":"NOT_COMPUTED","blank_or_uniform_posteriors_written":False})
print(decision["DEVELOPMENT_DECISION"])
