#!/usr/bin/env python3
"""C2 diagnostic: compare the deployable M1 temporal provider to GADEN traces."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common.map_geometry import load_map_info
from m1_causal.temporal_transport import replay_candidate_exposure
from m2_cpo.physical_prior import PhysicalPriorConfig


class Frame:
    def __init__(self, stamp_ns: int, pose_xy: tuple[float, float], wind_uv: tuple[float, float]):
        self.stamp_ns = stamp_ns
        self.pose_xy = pose_xy
        self.wind_uv = wind_uv


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def corr(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    a = [math.log1p(max(0.0, value)) for value in left]
    b = [math.log1p(max(0.0, value)) for value in right]
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va, vb = sum((x - ma) ** 2 for x in a), sum((x - mb) ** 2 for x in b)
    if va <= 1e-24 or vb <= 1e-24:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--maps", type=Path, required=True)
    parser.add_argument("--candidate-forward", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for house in ("H01", "H02", "H03"):
        manifest = json.loads((args.assets / "manifests" / f"{house}.json").read_text(encoding="utf-8"))
        episodes = {episode["episode_id"]: episode for episode in manifest["m1_episodes"]}
        nx, ny, free, ox, oy, dx = load_map_info(args.maps / house)
        config = PhysicalPriorConfig(nx=nx, ny=ny, dx=dx, diffusion=.01, free=free,
                                     origin_xy=(ox, oy), field_dt=.2, route_dt=.2,
                                     transport_time_scale=1., transport_backend="numpy")
        for case_id, episode in episodes.items():
            history_path = args.assets / episode["history_trace_path"]
            history = read_jsonl(history_path)
            bootstrap = Frame(0, tuple(float(v) for v in history[0]["pose_xy"]),
                              tuple(float(v) for v in history[0]["wind_uv"]))
            prefix = (bootstrap,) + tuple(Frame(int(row["stamp_ns"]), tuple(float(v) for v in row["pose_xy"]),
                                                    tuple(float(v) for v in row["wind_uv"])) for row in history)
            predicted = replay_candidate_exposure(prefix, config=config,
                                                   source_xy=tuple(float(v) for v in episode["source_xyz_m"][:2]))
            forward_path = args.candidate_forward / case_id / "candidate_forward_input.jsonl"
            expected_rows = read_jsonl(forward_path)
            expected = [float(row["candidate_forward_input_ppm"]) for row in expected_rows]
            if len(predicted) != len(expected):
                raise ValueError(f"M1_PROVIDER_ALIGNMENT_LENGTH:{case_id}")
            rows.append({"case_id": case_id, "house": house,
                         "provider_input_fields": ["stamp_ns", "pose_xy", "wind_uv", "candidate_xy"],
                         "forbidden_provider_fields": ["gas_ppm", "source_id", "future_wind", "House_feature"],
                         "history_sha256": sha(history_path), "candidate_forward_sha256": sha(forward_path),
                         "log1p_shape_correlation": corr(list(predicted), expected),
                         "predicted_nonzero_fraction": sum(value > 0 for value in predicted) / len(predicted),
                         "gaden_nonzero_fraction": sum(value > 0 for value in expected) / len(expected),
                         "provider_finite": all(math.isfinite(value) and value >= 0 for value in predicted)})
    by_house = {}
    for house in ("H01", "H02", "H03"):
        subset = [row for row in rows if row["house"] == house]
        values = [row["log1p_shape_correlation"] for row in subset if row["log1p_shape_correlation"] is not None]
        by_house[house] = {"cases": len(subset), "finite_cases": sum(row["provider_finite"] for row in subset),
                           "mean_shape_correlation": sum(values) / len(values) if values else None,
                           "undefined_shape_cases": len(subset) - len(values)}
    report = {"contract": "CSTAR_M1_TEMPORAL_PROVIDER_ALIGNMENT_DIAGNOSTIC_V1",
              "verdict": "DIAGNOSTIC_ONLY_NOT_C2_PASS",
              "configuration": {"diffusion": .01, "source_rate": 1., "dt_s": .2, "transport_backend": "numpy"},
              "rows": rows, "by_house": by_house,
              "limits": ["candidate coordinates are evaluator-supplied only for forward adequacy", "no gas enters provider",
                         "un-calibrated physical scale; correlation assesses temporal shape only", "not an online PMFS integration"]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])


if __name__ == "__main__":
    main()
