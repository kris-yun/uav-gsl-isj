"""Truth-conditioned adequacy diagnostic for the executable physical prior.

This deliberately is **not** a qualification gate: evaluator source coordinates
are used only to ask whether the forward prior can score a held-out future
trace at all. No posterior, planner, bank or closed-loop result is produced.
The diagnostic is useful before an expensive run because a structurally wrong
physical prior should be repaired rather than hidden behind a learned residual.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import hashlib
from pathlib import Path
import sys

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from m1_picr.route_law_score import innovation_loglik
from m2_cpo.physical_prior import PhysicalCPOProvider, PhysicalPriorConfig
from common.map_geometry import load_map_info


class Frame:
    def __init__(self, row):
        self.stamp_ns = int(row["stamp_ns"])
        self.pose_xy = tuple(float(v) for v in row["pose_xy"])
        self.gas_ppm = float(row["gas_ppm"])
        self.wind_uv = tuple(float(v) for v in row["wind_uv"])


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def route_points(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return tuple((float(r["x"]), float(r["y"])) for r in rows[1:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", type=Path, required=True)
    ap.add_argument("--maps", type=Path, required=True)
    ap.add_argument("--routes", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--max-cases", type=int, default=3)
    ap.add_argument("--houses", default="H01,H02,H03")
    ap.add_argument("--assimilate-prefix", action="store_true",
                    help="use the causal prefix-only source-strength state")
    ap.add_argument('--clock', type=Path, help='bind transport/sensor time ratio to the environment contract')
    ap.add_argument('--condition-noise-free-sensor', action='store_true')
    ap.add_argument('--sensor-manifest',type=Path)
    ap.add_argument('--vectorized-transport',action='store_true')
    args = ap.parse_args()
    source_paths=[Path(__file__),HERE/'m2_cpo/physical_prior.py',HERE/'common/map_geometry.py',
                  HERE/'validate_environment_alignment_v2.py',HERE/'m1_picr/route_law_score.py']
    code_identity={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    clock = json.loads(args.clock.read_text()) if args.clock else None
    time_scale = float(clock['field_replay_speed_ratio']) if clock else 1.0
    if clock and not math.isclose(clock['sensor_dt_s']*time_scale,clock['stored_field_dt_s']):
        raise ValueError('CSTAR_PRIOR_DIAGNOSTIC_CLOCK')
    if args.condition_noise_free_sensor:
        if args.sensor_manifest is None:
            raise ValueError('CSTAR_PRIOR_DIAGNOSTIC_SENSOR_CONTRACT_REQUIRED')
        sensor_contract=json.loads(args.sensor_manifest.read_text())['sensor']['config']
        expected={'noise_std_ppm':0.,'gain':1.,'baseline':0.,'drift_rate_ppm_s':0.,
                  'tau_rise_s':1.2,'tau_recovery_s':1.2,'dead_time_s':.4,
                  'saturation_max_ppm':1e6,'saturation_min_ppm':0.}
        if any(not math.isclose(float(sensor_contract[k]),v) for k,v in expected.items()):
            raise ValueError('CSTAR_PRIOR_DIAGNOSTIC_SENSOR_NOT_NOISE_FREE_FOPDT')
    if args.max_cases < 1:
        raise ValueError("CSTAR_PRIOR_DIAGNOSTIC_CASE_LIMIT")
    rows = []
    failures = []
    houses = tuple(h.strip() for h in args.houses.split(",") if h.strip())
    if not houses or any(h not in {"H01", "H02", "H03"} for h in houses):
        raise ValueError("CSTAR_PRIOR_DIAGNOSTIC_HOUSES")
    for house in houses:
        manifest = json.loads((args.assets / "manifests" / f"{house}.json").read_text(encoding="utf-8"))
        width, height, free, ox, oy, resolution = load_map_info(args.maps / house)
        episodes = {r["episode_id"]: r for r in manifest["m1_episodes"]}
        attempted = 0
        for case in manifest["m2_route_cases"]:
            # Each LOHO manifest is complete and contains cases for all three
            # physical Houses.  The diagnostic map/route pair must follow the
            # case's authoritative House, not the outer-fold filename.
            if case["house"] != house:
                continue
            if attempted >= args.max_cases:
                break
            attempted += 1
            ep = episodes[case["episode_id"]]
            history = read_jsonl(args.assets / ep["history_trace_path"])
            prefix_rows = [r for r in history if float(r["t_sim_s"]) <= case["decision_time_s"]]
            outcome = read_jsonl(args.assets / case["outcome_trace_path"])
            route = route_points(args.routes / house / Path(case["planned_route_path"]).name)
            if len(route) != len(outcome):
                raise ValueError("CSTAR_PRIOR_DIAGNOSTIC_ROUTE_OUTCOME_LENGTH")
            # The archived trace starts at 0.2 s; duplicate its first frame as
            # bootstrap so the replay starts with the declared zero state.
            bootstrap = dict(prefix_rows[0], stamp_ns=0, gas_ppm=0.0)
            prefix = [Frame(bootstrap)] + [Frame(r) for r in prefix_rows]
            try:
                provider = PhysicalCPOProvider(PhysicalPriorConfig(
                    nx=width, ny=height, dx=resolution, diffusion=0.01, free=free,
                    origin_xy=(ox, oy), field_dt=0.5, route_dt=0.2,
                    transport_time_scale=time_scale,
                    condition_noise_free_sensor=args.condition_noise_free_sensor,
                    transport_backend='numpy' if args.vectorized_transport else 'reference',
                    sensor_tau=1.2, sensor_dead=0.4, source_rate_values=(0.5, 1.0, 2.0)))
                request = type("Request", (), {"source_xy": tuple(ep["source_xyz_m"][:2]),
                                               "route_xy": route})()
                candidate = ((provider.predict_assimilated(prefix, request),), (1.0,)) \
                    if args.assimilate_prefix else provider.predict_ensemble(prefix, request)
                context = provider.predict_context(prefix, route)
            except ValueError as exc:
                failures.append({"house": house, "decision_id": case["decision_id"],
                                 "error": str(exc),
                                 "interpretation": "map/route alignment must be repaired before a physical gate"})
                continue
            observed = [math.log1p(float(r["gas_ppm"])) for r in outcome]
            valid = torch.ones(len(observed), dtype=torch.bool)
            # Fixed source-rate ensemble is marginalized; source coordinate is
            # evaluator-only in this diagnostic, never a runtime input.
            source_scores = []
            for law in candidate[0]:
                source_scores.append(innovation_loglik(
                    torch.tensor(observed), torch.tensor(law.logppm_mean),
                    torch.tensor(law.logppm_scale), valid, rho=0.3))
            source_nll = -float(torch.logsumexp(torch.stack(source_scores) - math.log(len(source_scores)), 0))
            context_nll = -float(innovation_loglik(
                torch.tensor(observed), torch.tensor(context.logppm_mean),
                torch.tensor(context.logppm_scale), valid, rho=0.3))
            persistence_nll = -float(innovation_loglik(
                torch.tensor(observed), torch.full((len(observed),),math.log1p(prefix[-1].gas_ppm)),
                torch.ones(len(observed)), valid, rho=0.3))
            matched_scale_scores=[innovation_loglik(torch.tensor(observed),torch.tensor(l.logppm_mean),
                                                   torch.ones(len(observed)),valid,rho=.3) for l in candidate[0]]
            matched_scale_nll=-float(torch.logsumexp(torch.stack(matched_scale_scores)-math.log(len(matched_scale_scores)),0))
            forecast_mean=[sum(l.logppm_mean[i] for l in candidate[0])/len(candidate[0]) for i in range(len(observed))]
            last_log=math.log1p(prefix[-1].gas_ppm)
            rows.append({"house": house, "decision_id": case["decision_id"],
                         'history_sha256':hashlib.sha256((args.assets/ep['history_trace_path']).read_bytes()).hexdigest(),
                         'outcome_sha256':hashlib.sha256((args.assets/case['outcome_trace_path']).read_bytes()).hexdigest(),
                         'observed_logppm':observed,
                         'source_components':[{'mean':list(l.logppm_mean),'scale':list(l.logppm_scale)} for l in candidate[0]],
                         'context_mean':list(context.logppm_mean),'context_scale':list(context.logppm_scale),
                         "source_conditioned_nll": source_nll,
                         "context_nll": context_nll,
                         "increment_context_minus_source": context_nll - source_nll,
                         "persistence_nll": persistence_nll,
                         "increment_persistence_minus_source": persistence_nll - source_nll,
                         'source_matched_scale_nll':matched_scale_nll,
                         'matched_scale_increment':persistence_nll-matched_scale_nll,
                         'source_logppm_mse':sum((x-y)**2 for x,y in zip(forecast_mean,observed))/len(observed),
                         'persistence_logppm_mse':sum((last_log-y)**2 for y in observed)/len(observed),
                         "latest_observed_ppm": prefix[-1].gas_ppm,
                         "observed_first_hit": next((i for i, r in enumerate(outcome)
                                                      if float(r["gas_ppm"]) > 0.1), len(outcome)),
                         "route_steps": len(route)})
    final_code_identity={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    if final_code_identity!=code_identity:
        raise ValueError('CSTAR_DIAGNOSTIC_PRODUCER_CHANGED_DURING_RUN')
    summaries=[]
    for house in houses:
        cases=[r for r in rows if r['house']==house]
        if cases:
            summaries.append({'house':house,'cases':len(cases),**{
                k:sum(r[k] for r in cases)/len(cases) for k in
                ['increment_persistence_minus_source','matched_scale_increment','source_logppm_mse','persistence_logppm_mse']}})
    report = {
        "contract": "CSTAR_M2_PHYSICAL_PRIOR_TRUTH_CONDITIONED_DIAGNOSTIC_V1",
        "verdict": "DIAGNOSTIC_ONLY_NOT_FORMAL_GATE",
        "source_truth_runtime_input": False,
        "source_truth_evaluator_conditioning": True,
        "source_rate_marginalization": [0.5, 1.0, 2.0],
        "prefix_amplitude_assimilation": bool(args.assimilate_prefix),
        'transport_time_scale': time_scale,
        'condition_noise_free_sensor': args.condition_noise_free_sensor,
        'clock_sha256': hashlib.sha256(args.clock.read_bytes()).hexdigest() if args.clock else None,
        'sensor_manifest_sha256': hashlib.sha256(args.sensor_manifest.read_bytes()).hexdigest() if args.sensor_manifest else None,
        'source_code_sha256': code_identity,
        'transport_backend': 'numpy' if args.vectorized_transport else 'reference',
        'summaries':summaries,
        "diffusion": 0.01,
        "sensor": {"tau_s": 1.2, "dead_s": 0.4, "route_dt_s": 0.2},
        "cases": rows,
        "failures": failures,
        "limitations": [
            "source coordinate is supplied only for forward adequacy scoring",
            "initial field is declared zero and no bank is queried",
            "does not qualify candidate-support localization or controller utility",
            "does not authorize House123 closed loop",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["verdict"], len(rows))
    print(json.dumps(summaries),flush=True)


if __name__ == "__main__":
    main()
