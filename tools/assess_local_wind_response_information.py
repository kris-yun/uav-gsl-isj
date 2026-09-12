"""Source-blind, local-only input gate for a prospective wind-response module.

This is not an instrumental-variable validity test or a source estimator.
The pandas CSV parser imports only an explicit deployment-field whitelist;
gas truth and source labels never enter a parsed data frame. Full-file bytes
are hashed for provenance, not interpreted as observations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd


HOUSES = ("H01", "H02", "H03")
HORIZON_S = 240.0
DT_S = 0.2
TIME_TOLERANCE_S = 1e-8
MIN_STOP_SAMPLES = 10
GRAM_RANK_ATOL = 1e-12
RESPONSE_CHANGE_ATOL = 1e-12
RESPONSE_LAG_SAMPLES = 1
FIELDS = {
    "sensor_trace.csv": ("t_sim_s", "step", "measured_gas_ppm"),
    "wind_trace.csv": ("t_sim_s", "step", "wind_u", "wind_v"),
    "sim_pose_trace.csv": ("t_sim_s", "step", "x", "y", "z", "is_moving"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_projected_prefix(path: Path, fields: tuple[str, ...]) -> pd.DataFrame:
    """Only timestamps are inspected to stop before post-budget observations.

    These archived traces have timestamp as the first column. We require that
    exact format rather than guessing. Prefix CSV text is passed to usecols;
    non-whitelisted observation columns are never imported or accessed.
    """
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header_line = handle.readline()
        header = next(csv.reader([header_line]))
        if len(header) != len(set(header)) or not header or header[0] != "t_sim_s":
            raise ValueError(f"UNSUPPORTED_OR_DUPLICATE_HEADER:{path.name}")
        if not set(fields).issubset(header):
            raise ValueError(f"MISSING_WHITELIST_FIELDS:{path.name}")
        prefix_lines = [header_line]
        last_time = None
        for line in handle:
            time_s = float(line.split(",", 1)[0])
            if not np.isfinite(time_s) or time_s < 0:
                raise ValueError(f"INVALID_TIMESTAMP:{path.name}")
            if last_time is not None and time_s <= last_time:
                raise ValueError(f"NONINCREASING_TIMESTAMP:{path.name}")
            if time_s > HORIZON_S:
                break
            prefix_lines.append(line)
            last_time = time_s
    frame = pd.read_csv(io.StringIO("".join(prefix_lines)), usecols=list(fields),
                        dtype={name: "float64" for name in fields})
    if set(frame.columns) != set(fields) or frame.empty:
        raise ValueError(f"EMPTY_OR_UNEXPECTED_PROJECTED_COLUMNS:{path.name}")
    frame = frame.loc[:, list(fields)]
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError(f"NONFINITE_DEPLOYMENT_FIELDS:{path.name}")
    if np.any(frame["step"].to_numpy() != np.floor(frame["step"].to_numpy())):
        raise ValueError(f"NONINTEGER_STEP:{path.name}")
    if np.any(np.diff(frame["step"].to_numpy()) <= 0):
        raise ValueError(f"NONINCREASING_STEP:{path.name}")
    return frame


def stationary_segments(pose: pd.DataFrame) -> list[list[int]]:
    """Maximal stationary exact-printed-pose segments; no gas/wind selection."""
    time = pose["t_sim_s"].to_numpy()
    step = pose["step"].to_numpy()
    xyz = pose[["x", "y", "z"]].to_numpy()
    moving = pose["is_moving"].to_numpy()
    if not np.isin(moving, (0, 1)).all():
        raise ValueError("INVALID_IS_MOVING")
    segments: list[list[int]] = []
    active: list[int] = []
    for index in range(len(time)):
        if moving[index] != 0:
            if active:
                segments.append(active)
            active = []
            continue
        if active:
            previous = active[-1]
            contiguous = (abs(time[index] - time[previous] - DT_S) <= TIME_TOLERANCE_S
                          and step[index] == step[previous] + 1)
            if not contiguous or not np.array_equal(xyz[index], xyz[previous]):
                segments.append(active)
                active = []
        active.append(index)
    if active:
        segments.append(active)
    return segments


def assess_run(run_dir: Path) -> dict:
    frames = {name: read_projected_prefix(run_dir / name, fields)
              for name, fields in FIELDS.items()}
    sensor = frames["sensor_trace.csv"]
    wind = frames["wind_trace.csv"]
    pose = frames["sim_pose_trace.csv"]
    alignment = sensor[["t_sim_s", "step"]].to_numpy()
    if not all(np.array_equal(alignment, frames[name][["t_sim_s", "step"]].to_numpy())
               for name in FIELDS):
        raise ValueError("TIMESTAMP_OR_STEP_ALIGNMENT_FAILURE")
    if np.any(sensor["measured_gas_ppm"].to_numpy() < 0):
        raise ValueError("NEGATIVE_MEASURED_GAS")
    if (len(alignment) != round(HORIZON_S / DT_S)
            or not np.allclose(alignment[:, 0], np.arange(1, len(alignment) + 1) * DT_S,
                               atol=TIME_TOLERANCE_S, rtol=0)):
        raise ValueError("INCOMPLETE_FIXED_0_TO_240S_INPUT")
    segments = stationary_segments(pose)
    reports = []
    for stop_id, indices in enumerate(segments):
        if len(indices) < MIN_STOP_SAMPLES:
            continue
        xyzw = pose.iloc[indices][["x", "y", "z"]].to_numpy()
        uv = wind.iloc[indices][["wind_u", "wind_v"]].to_numpy()
        gas = sensor.iloc[indices]["measured_gas_ppm"].to_numpy()
        loggas = np.log1p(gas)  # concentration divided by the declared 1 ppm reference
        z = np.diff(uv, axis=0)  # a difference; not a certified exogenous innovation
        response = np.diff(loggas)
        gram = z.T @ z
        eigenvalues = np.linalg.eigvalsh(gram)
        rank = int(np.count_nonzero(eigenvalues > GRAM_RANK_ATOL))
        pairs_z = z[:-RESPONSE_LAG_SAMPLES]
        pairs_response = response[RESPONSE_LAG_SAMPLES:]
        cross_moment = (pairs_z.T @ pairs_response) / len(pairs_response)
        changed = int(np.count_nonzero(np.abs(response) > RESPONSE_CHANGE_ATOL))
        reports.append({
            "geometry_stop_id": stop_id,
            "first_step": int(alignment[indices[0], 1]),
            "last_step": int(alignment[indices[-1], 1]),
            "start_s": float(alignment[indices[0], 0]),
            "end_s": float(alignment[indices[-1], 0]),
            "samples": len(indices), "printed_pose_xyz_m": xyzw[0].tolist(),
            "wind_difference_samples": len(z),
            "wind_difference_gram": gram.tolist(),
            "wind_difference_gram_eigenvalues": eigenvalues.tolist(),
            "wind_difference_numerical_rank": rank,
            "wind_difference_gram_condition_number": (
                float(eigenvalues[-1] / eigenvalues[0]) if rank == 2 else None),
            "measured_gas_range_ppm": [float(gas.min()), float(gas.max())],
            "log1p_measured_gas_variance": float(np.var(loggas)),
            "log1p_response_changed_steps": changed,
            "log1p_response_rms": float(np.sqrt(np.mean(response ** 2))),
            "gas_above_0_1ppm_samples_descriptive_only": int(np.count_nonzero(gas > 0.1)),
            "lag_one_wind_difference_gas_increment_pairs": len(pairs_response),
            "lag_one_raw_cross_moment_descriptive_only": cross_moment.tolist(),
            "input_richness_available": bool(rank == 2 and changed > 0),
        })
    rich_count = sum(item["input_richness_available"] for item in reports)
    return {
        "status": ("OBSERVABLE_INFORMATION_AVAILABLE" if rich_count
                   else "INSUFFICIENT_OBSERVABLE_INFORMATION"),
        "input_sha256": {name: sha256(run_dir / name) for name in FIELDS},
        "loaded_columns": {name: list(fields) for name, fields in FIELDS.items()},
        "aligned_samples": len(sensor),
        "first_time_s": float(alignment[0, 0]), "last_time_s": float(alignment[-1, 0]),
        "maximal_geometry_stop_segments": len(segments),
        "segments_below_minimum_samples": sum(len(s) < MIN_STOP_SAMPLES for s in segments),
        "eligible_stop_segments": len(reports),
        "rank_two_stop_segments": sum(r["wind_difference_numerical_rank"] == 2 for r in reports),
        "rank_two_and_nonconstant_gas_stop_segments": rich_count,
        "rank_two_and_gas_above_0_1ppm_segments_descriptive_only": sum(
            r["wind_difference_numerical_rank"] == 2
            and r["gas_above_0_1ppm_samples_descriptive_only"] > 0 for r in reports),
        "stops": reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    repo = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path,
                        default=repo / "evidence/m1r_instrumented_20260912")
    parser.add_argument("--output", type=Path,
                        default=repo / "evidence/m1r_causal_repair_20260912/WIND_RESPONSE_INFORMATION_GATE.json")
    args = parser.parse_args()
    runs = {}
    for house in HOUSES:
        name = f"{house}_seed12_M1R"
        try:
            runs[name] = assess_run(args.root / name)
        except (ValueError, OSError, pd.errors.ParserError) as error:
            runs[name] = {"status": "INSUFFICIENT_OBSERVABLE_INFORMATION", "error": str(error)}
    available = all(r["status"] == "OBSERVABLE_INFORMATION_AVAILABLE" for r in runs.values())
    report = {
        "contract": "LOCAL_WIND_RESPONSE_INFORMATION_GATE_V1",
        "scientific_status": "CAUSAL_ADMISSION_NOT_ESTABLISHED",
        "status": ("OBSERVABLE_INFORMATION_AVAILABLE" if available
                   else "INSUFFICIENT_OBSERVABLE_INFORMATION"),
        "script_sha256": sha256(Path(__file__)), "input_root": str(args.root.resolve()),
        "frozen_analysis_config": {
            "horizon_s": HORIZON_S, "sample_dt_s": DT_S,
            "time_tolerance_s": TIME_TOLERANCE_S, "minimum_stop_samples": MIN_STOP_SAMPLES,
            "gram_rank_absolute_tolerance": GRAM_RANK_ATOL,
            "gas_increment_change_absolute_tolerance": RESPONSE_CHANGE_ATOL,
            "response_lag_samples": RESPONSE_LAG_SAMPLES,
            "gas_reference_ppm": 1.0,
            "segment_selection": "maximal same printed xyz, is_moving=0, contiguous time and step; no gas/wind selection",
            "availability_rule": "each House has at least one eligible stop with wind-difference rank 2 and a nonconstant measured gas trace",
            "parameter_search": False,
            "evaluation_role": "development input audit; not preregistered confirmatory efficacy evidence",
        },
        "claims": {"source_labels_used": False, "gas_truth_loaded": False,
                   "instrument_exogeneity_pass": False, "source_identification_pass": False,
                   "proper_source_evidence_pass": False, "causal_main_innovation_pass": False,
                   "closed_loop_utility_pass": False},
        "limitations": [
            "Wind differences are not certified martingale innovations or exogenous instruments.",
            "Nonconstant gas and rank-two wind variation do not establish wind-caused gas response; the cross moment is descriptive.",
            "Measurement noise or shared upstream transport can generate apparent variation or association.",
            "Local wind W measures a latent spatial flow F: F may cause both W and gas. Intervening on a reading W is not intervening on F.",
            "W=U,Y=beta*W+epsilon and W=U,Y=beta*U+epsilon are observationally identical but have different do(W) effects; covariance cannot resolve them.",
            "Correlated samples and stops from one run are not independent realizations.",
            "CSV coordinate equality is only equality at printed precision; no causal action randomization is assumed.",
            "There is no candidate source response, source alias exclusion, calibrated likelihood, or efficacy evaluation in this gate.",
            "An adaptive PMFS route requires conditioning on legal history; fixed-route information is not closed-loop utility.",
        ],
        "next_minimal_falsifiable_test": (
            "First establish an independently justified measurement/causal model linking local wind W to a real spatial flow perturbation F; "
            "a do(W) reading change is not a do(F) intervention, and more wind-provider tuning does not resolve this missing identification assumption. "
            "Only after that, freeze the mapping from a local wind innovation to the declared spatial transport perturbation, "
            "then generate source-conditioned response derivative vectors using only legal prefixes and map geometry. "
            "Freeze those vectors before evaluator-only alias labels are used. Test every preserved H01/H02 source alias "
            "after the same predeclared nuisance removal. Identical or zero response vectors, all-abstention, or an "
            "unjustified wind-intervention mapping stop causal admission; do not substitute a geometric source-direction score."
        ),
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "runs": {
        name: {key: item.get(key) for key in ("status", "aligned_samples", "eligible_stop_segments",
                    "rank_two_and_nonconstant_gas_stop_segments", "error")}
        for name, item in runs.items()}}, ensure_ascii=False))
    return 0 if available else 1


if __name__ == "__main__":
    raise SystemExit(main())
