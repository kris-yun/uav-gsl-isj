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
from pathlib import Path
import sys

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from m1_picr.route_law_score import innovation_loglik
from m2_cpo.physical_prior import PhysicalCPOProvider, PhysicalPriorConfig


class Frame:
    def __init__(self, row):
        self.stamp_ns = int(row["stamp_ns"])
        self.pose_xy = tuple(float(v) for v in row["pose_xy"])
        self.gas_ppm = float(row["gas_ppm"])
        self.wind_uv = tuple(float(v) for v in row["wind_uv"])


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_pgm(path: Path):
    raw = path.read_bytes()
    if not raw.startswith(b"P5"):
        raise ValueError("CSTAR_PRIOR_DIAGNOSTIC_PGM")
    parts, i = [], 2
    while len(parts) < 3:
        while i < len(raw) and raw[i] in b" \t\r\n": i += 1
        if raw[i:i + 1] == b"#":
            i = raw.find(b"\n", i) + 1
            continue
        j = i
        while j < len(raw) and raw[j] not in b" \t\r\n": j += 1
        parts.append(int(raw[i:j])); i = j
    width, height, maximum = parts
    if maximum != 255 or len(raw) - i < width * height:
        raise ValueError("CSTAR_PRIOR_DIAGNOSTIC_PGM_SIZE")
    pixels = raw[i:i + width * height]
    # PGM row zero is the top of the image; the physical map origin is bottom.
    free = [False] * (width * height)
    for row in range(height):
        for x in range(width):
            y = height - 1 - row
            free[x + y * width] = pixels[row * width + x] > 0
    return width, height, tuple(free)


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
    args = ap.parse_args()
    if args.max_cases < 1:
        raise ValueError("CSTAR_PRIOR_DIAGNOSTIC_CASE_LIMIT")
    rows = []
    failures = []
    houses = tuple(h.strip() for h in args.houses.split(",") if h.strip())
    if not houses or any(h not in {"H01", "H02", "H03"} for h in houses):
        raise ValueError("CSTAR_PRIOR_DIAGNOSTIC_HOUSES")
    for house in houses:
        manifest = json.loads((args.assets / "manifests" / f"{house}.json").read_text(encoding="utf-8"))
        width, height, free = read_pgm(args.maps / house / "navigation_slice.pgm")
        yaml_lines = (args.maps / house / "navigation_slice.yaml").read_text(encoding="utf-8").splitlines()
        origin = next(i for i, line in enumerate(yaml_lines) if line.startswith("origin:"))
        ox = float(yaml_lines[origin + 1].split("-", 1)[1].strip())
        oy = float(yaml_lines[origin + 2].split("-", 1)[1].strip())
        episodes = {r["episode_id"]: r for r in manifest["m1_episodes"]}
        attempted = 0
        for case in manifest["m2_route_cases"]:
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
            prefix = [Frame(prefix_rows[0])] + [Frame(r) for r in prefix_rows]
            try:
                provider = PhysicalCPOProvider(PhysicalPriorConfig(
                    nx=width, ny=height, dx=0.1, diffusion=0.01, free=free,
                    origin_xy=(ox, oy), field_dt=0.5, route_dt=0.2,
                    sensor_tau=1.2, sensor_dead=0.4, source_rate_values=(0.5, 1.0, 2.0)))
                request = type("Request", (), {"source_xy": tuple(ep["source_xyz_m"][:2]),
                                               "route_xy": route})()
                candidate = provider.predict_ensemble(prefix, request)
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
            rows.append({"house": house, "decision_id": case["decision_id"],
                         "source_conditioned_nll": source_nll,
                         "context_nll": context_nll,
                         "increment_context_minus_source": context_nll - source_nll,
                         "observed_first_hit": next((i for i, r in enumerate(outcome)
                                                      if float(r["gas_ppm"]) > 0.1), len(outcome)),
                         "route_steps": len(route)})
    report = {
        "contract": "CSTAR_M2_PHYSICAL_PRIOR_TRUTH_CONDITIONED_DIAGNOSTIC_V1",
        "verdict": "DIAGNOSTIC_ONLY_NOT_FORMAL_GATE",
        "source_truth_runtime_input": False,
        "source_truth_evaluator_conditioning": True,
        "source_rate_marginalization": [0.5, 1.0, 2.0],
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


if __name__ == "__main__":
    main()
