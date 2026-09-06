from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cstar_reference import prospective_resolution_scores


def choose(posterior, route_laws) -> tuple[int, float]:
    scores = prospective_resolution_scores(posterior, route_laws)
    selected = max(scores, key=lambda item: (item.resolution, -item.route_index))
    return selected.route_index, selected.resolution


def destructive_route_shuffle(route_laws):
    """Deterministically break route-law identity without changing law values.

    Each source row is cyclically shifted by a source-dependent nonzero amount.
    The outcome distributions are preserved, but their association to physical
    route indices is destroyed. This is a mechanism falsifier, not a baseline.
    """
    route_count = len(route_laws[0])
    if route_count < 2:
        raise RuntimeError("CSTAR_M3_NEEDS_AT_LEAST_2_ROUTES")
    shuffled = []
    for source_index, row in enumerate(route_laws):
        if len(row) != route_count:
            raise RuntimeError("CSTAR_M3_ROUTE_SHAPE")
        shift = (source_index % (route_count - 1)) + 1
        shuffled.append(row[shift:] + row[:shift])
    return shuffled


def summarize(deltas: list[float]) -> dict:
    wins = sum(delta < 0.0 for delta in deltas)
    losses = sum(delta > 0.0 for delta in deltas)
    ties = len(deltas) - wins - losses
    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "mean_risk_delta": sum(deltas) / len(deltas),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    if not args.panel.is_file():
        report = {
            "contract": "CSTAR_M3_COUNTERFACTUAL_GATE_V1",
            "pass": False,
            "verdict": "M3_REAL_GATE_BLOCKED_ASSET_MISSING",
            "required_asset": "same decision context x >=2 feasible routes x independent realized outcomes",
            "panel": str(args.panel),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(report["verdict"])
        return 3

    data = json.loads(args.panel.read_text(encoding="utf-8"))
    if data.get("contract") != "CSTAR_M3_COUNTERFACTUAL_PANEL_V1":
        raise RuntimeError("CSTAR_M3_PANEL_CONTRACT")
    cases = data.get("cases", [])
    if not cases:
        raise RuntimeError("CSTAR_M3_PANEL_EMPTY")

    real_deltas: list[float] = []
    shuffled_deltas: list[float] = []
    details = []
    for case in cases:
        posterior = case["posterior"]
        route_laws = case["route_laws"]
        native = int(case["native_route"])
        risk = [float(value) for value in case["realized_source_risk"]]
        if not risk or native < 0 or native >= len(risk):
            raise RuntimeError("CSTAR_M3_NATIVE_OR_RISK_SHAPE")
        if any(not math.isfinite(value) for value in risk):
            raise RuntimeError("CSTAR_M3_NONFINITE_RISK")

        chosen, resolution = choose(posterior, route_laws)
        if chosen >= len(risk):
            raise RuntimeError("CSTAR_M3_CHOSEN_ROUTE_RISK_MISSING")
        real_delta = risk[chosen] - risk[native]
        real_deltas.append(real_delta)

        shuffled_laws = destructive_route_shuffle(route_laws)
        shuffled_chosen, shuffled_resolution = choose(posterior, shuffled_laws)
        shuffled_delta = risk[shuffled_chosen] - risk[native]
        shuffled_deltas.append(shuffled_delta)

        details.append({
            "id": case.get("id"),
            "chosen_route": chosen,
            "native_route": native,
            "chosen_resolution": resolution,
            "risk_delta": real_delta,
            "shuffled_chosen_route": shuffled_chosen,
            "shuffled_resolution": shuffled_resolution,
            "shuffled_risk_delta": shuffled_delta,
        })

    real = summarize(real_deltas)
    shuffled = summarize(shuffled_deltas)
    mechanism_destroyed = bool(
        shuffled["wins"] < real["wins"]
        and shuffled["mean_risk_delta"] > real["mean_risk_delta"] + 1e-12
    )
    actual_benefit = bool(real["wins"] > real["losses"] and real["mean_risk_delta"] < 0.0)
    passed = actual_benefit and mechanism_destroyed

    report = {
        "contract": "CSTAR_M3_COUNTERFACTUAL_GATE_V1",
        "cases": len(cases),
        "real": real,
        "destructive_route_law_shuffle": shuffled,
        "actual_benefit": actual_benefit,
        "mechanism_destroyed_by_shuffle": mechanism_destroyed,
        "pass": passed,
        "verdict": "M3_COUNTERFACTUAL_PASS" if passed else "M3_COUNTERFACTUAL_NO_GO",
        "details": details,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
