#!/usr/bin/env python3
"""Frozen WCIG R0: existing wind fields plus existing LSC edge energies only."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/source_lineage_lagrangian_v2"))
sys.path.insert(0, str(ROOT / "research/local_stochastic_confusability_v0"))
from export_gaden_wind_3d import export_one  # validated GADEN binary/layout reader
from l1_filament_transition_audit import read_occ, sample_wind, state_at
from analyze_lsc_crosswind_d0 import SOURCE_IDS, edges_from_panel

WINDS = (
    ("W0", "3,5-1_slow"),
    ("W1", "3,5-1_fast"),
    ("W2", "4,5-3_slow"),
    ("W3", "4,5-3_fast"),
)
RESULT_KEYS = {
    "W0": "W0_D1R_anchor",
    "W1": "W1_3,5-1_fast",
    "W2": "W2_4,5-3_slow",
}
EPS = 1e-6
EXPECTED = {
    "inventory": "dec3b877783b606fc3bd1fceaa06acb32e6616b2cae2d2f2e2f7f52fc4ed71fb",
    "occupancy": "9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d",
    "panel": "71c2aa0680d9fb8d317def1d76168792f579427211d3ab0041870368cd6072f4",
    "lsc_result": "c545e5e4a2db547ddbb1be5e2e173d4f8532a6b1d0789ad5442b4f476d627dd82",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def checked_sha(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(f"SHA256 drift {path}: {actual} != {expected}")


def rho(x: np.ndarray, y: np.ndarray) -> float:
    value = float(spearmanr(x, y)[0])
    if not np.isfinite(value):
        raise RuntimeError("undefined Spearman correlation")
    return value


def design(features: np.ndarray) -> np.ndarray:
    if features.shape[1] != 3 or (features < 0).any():
        raise ValueError("invalid physical features")
    return np.column_stack((np.ones(len(features)), np.log(features + EPS)))


def orientation(values: np.ndarray, is_x: np.ndarray) -> dict:
    x = float(np.mean(values[is_x]))
    y = float(np.mean(values[~is_x]))
    return {"x_mean": x, "y_mean": y, "x_minus_y": x - y,
            "ordering": "x>y" if x > y else ("y>x" if y > x else "tie")}


def loow_loglinear(features: np.ndarray, energy: np.ndarray,
                   is_x: np.ndarray) -> dict:
    x = design(features)
    if (energy <= 0).any():
        raise ValueError("energy distance must be positive for log target")
    y = np.log(energy)
    predicted = np.full(30, np.nan)
    folds = {}
    for wi, (label, _) in enumerate(WINDS[:3]):
        test = np.arange(wi * 10, (wi + 1) * 10)
        train = np.setdiff1d(np.arange(30), test)
        beta, _, matrix_rank, singular = np.linalg.lstsq(x[train], y[train], rcond=None)
        predicted[test] = x[test] @ beta
        obs_orient = orientation(energy[test], is_x)
        pred_orient = orientation(np.exp(predicted[test]), is_x)
        folds[label] = {
            "rho": rho(predicted[test], y[test]),
            "coefficients": [float(v) for v in beta],
            "design_rank": int(matrix_rank),
            "singular_values": [float(v) for v in singular],
            "observed_orientation": obs_orient,
            "predicted_orientation": pred_orient,
            "orientation_matches": pred_orient["ordering"] == obs_orient["ordering"],
        }
    assert np.isfinite(predicted).all()
    pattern = (folds["W0"]["observed_orientation"]["ordering"] == "y>x"
               and folds["W1"]["observed_orientation"]["ordering"] == "y>x"
               and folds["W2"]["observed_orientation"]["ordering"] == "x>y")
    return {
        "pooled_rho": rho(predicted, y),
        "folds": folds,
        "observed_family_reversal": bool(pattern),
        "predicted_family_reversal": bool(pattern and all(
            fold["orientation_matches"] for fold in folds.values())),
        "predicted_log_energy": predicted.tolist(),
    }


def loow_rank_only(features: np.ndarray, energy: np.ndarray) -> dict:
    # Within-wind ranks remove wind-scale information; only two physical ranks enter.
    xx = np.zeros((30, 3), dtype=float)
    yy = np.zeros(30, dtype=float)
    xx[:, 0] = 1.0
    for wi in range(3):
        sl = slice(wi * 10, (wi + 1) * 10)
        xx[sl, 1] = rankdata(features[sl, 0])
        xx[sl, 2] = rankdata(features[sl, 1])
        yy[sl] = rankdata(energy[sl])
    predicted = np.full(30, np.nan)
    folds = {}
    for wi, (label, _) in enumerate(WINDS[:3]):
        test = np.arange(wi * 10, (wi + 1) * 10)
        train = np.setdiff1d(np.arange(30), test)
        beta = np.linalg.lstsq(xx[train], yy[train], rcond=None)[0]
        predicted[test] = xx[test] @ beta
        folds[label] = {"rho": rho(predicted[test], yy[test]),
                        "coefficients": [float(v) for v in beta]}
    return {"pooled_rho": rho(predicted, yy), "folds": folds,
            "predicted_ranks": predicted.tolist()}


def local_wind_features(samples: np.ndarray, displacement: np.ndarray) -> dict:
    # samples [11 iterations, endpoint1/midpoint/endpoint2, xyz].
    local = (samples[:, 0] + 2 * samples[:, 1] + samples[:, 2]) / 4.0
    ubar = local.mean(axis=0)
    dhat = displacement[:2] / np.linalg.norm(displacement[:2])
    along = np.abs(local[:, :2] @ dhat)
    a_parallel = abs(float(ubar[:2] @ dhat))
    a_perp = abs(float(dhat[0] * ubar[1] - dhat[1] * ubar[0]))
    speed = float(np.linalg.norm(ubar[:2]))
    angles = np.arctan2(local[:, 1], local[:, 0])
    active = np.linalg.norm(local[:, :2], axis=1) > 1e-12
    if active.any():
        resultant = abs(np.mean(np.exp(1j * angles[active])))
        circular_sd = float(np.sqrt(-2 * np.log(max(resultant, 1e-12))))
    else:
        circular_sd = None
    asymmetry = float(np.linalg.norm(
        (samples[:, 0, :2] - samples[:, 2, :2]).mean(axis=0)))
    return {
        "A_parallel_mps": a_parallel,
        "A_perp_mps": a_perp,
        "U_mps": speed,
        "mean_wind_xyz_mps": [float(v) for v in ubar],
        "sd_abs_along_iteration_mps": float(np.std(along, ddof=0)),
        "circular_direction_sd_rad": circular_sd,
        "endpoint_mean_asymmetry_mps": asymmetry,
        "abs_mean_vertical_mps": abs(float(ubar[2])),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    inventory_path = ROOT / "evidence/causal_compositional_plume_world_model_v1/C0_5_HOUSE_WIND_INVENTORY_20260923.json"
    panel_path = ROOT / "evidence/local_stochastic_confusability_v0/crosswind_d0/LSC_CROSSWIND_D0_SOURCE_PANEL.tsv"
    result_path = ROOT / "evidence/local_stochastic_confusability_v0/crosswind_d0/LSC_CROSSWIND_D0_RESULT.json"
    checked_sha(inventory_path, EXPECTED["inventory"])
    checked_sha(panel_path, EXPECTED["panel"])
    checked_sha(result_path, EXPECTED["lsc_result"])
    inventory = json.loads(inventory_path.read_text())
    house = inventory["houses"]["House02"]
    occupancy_path = Path(house["occupancy"]["path"])
    checked_sha(occupancy_path, EXPECTED["occupancy"])
    env = read_occ(occupancy_path)
    assert tuple(house["occupancy"]["num_cells"]) == tuple(env["dims"])
    panel = pd.read_csv(panel_path, sep="\t")
    assert panel.source_id.tolist() == SOURCE_IDS and len(panel) == 8
    edges = edges_from_panel(panel)
    observed = json.loads(result_path.read_text())
    assert observed["gates"]["decision"] == "LSC_CROSSWIND_D0_FAIL_STOP_MAINLINE_GENERALITY"
    assert observed["source_ids"] == SOURCE_IDS and observed["edge_count"] == 10

    wind_samples = np.empty((4, 10, 11, 3, 3), dtype=np.float32)
    rows = []
    wind_hashes = []
    is_x = np.empty(10, dtype=bool)
    edge_ids = []
    for ei, (i, j) in enumerate(edges):
        a, b = panel.iloc[i], panel.iloc[j]
        displacement = np.array([b.x_m - a.x_m, b.y_m - a.y_m, b.z_m - a.z_m], float)
        assert np.isclose(np.linalg.norm(displacement[:2]), 0.30, atol=1e-5)
        is_x[ei] = abs(displacement[0]) > abs(displacement[1])
        edge_ids.append(f"{a.source_id}__{b.source_id}")

    for wi, (label, wind_name) in enumerate(WINDS):
        wind_info = house["wind_configs"][wind_name]
        wind_dir = Path(wind_info["path"])
        assert len(wind_info["iteration_records"]) == 11
        sequence, records = export_one(wind_dir, env["dims"])
        assert sequence.shape[0] == 11
        for r, expected in zip(records, wind_info["iteration_records"]):
            assert r["iteration"] == expected["iteration"]
            assert r["sha256"] == expected["sha256"]
            assert r["bytes"] == expected["size_bytes"]
            wind_hashes.append({"wind": label, "wind_name": wind_name,
                                "iteration": r["iteration"],
                                "path": str(wind_dir / f"wind_iteration_{r['iteration']}"),
                                "sha256": r["sha256"], "bytes": r["bytes"]})
        for ei, (i, j) in enumerate(edges):
            a, b = panel.iloc[i], panel.iloc[j]
            p1 = np.array([a.x_m, a.y_m, a.z_m], dtype=float)
            p2 = np.array([b.x_m, b.y_m, b.z_m], dtype=float)
            pmid = (p1 + p2) / 2.0
            states = [state_at(p, env) for p in (p1, pmid, p2)]
            if states != [0, 0, 0]:
                raise RuntimeError(f"nonfree source edge {edge_ids[ei]}: {states}")
            for k in range(11):
                wind_samples[wi, ei, k, 0] = sample_wind(sequence, k, p1, env)
                wind_samples[wi, ei, k, 1] = sample_wind(sequence, k, pmid, env)
                wind_samples[wi, ei, k, 2] = sample_wind(sequence, k, p2, env)
            displacement = p2 - p1
            f = local_wind_features(wind_samples[wi, ei].astype(float), displacement)
            row = {"wind": label, "wind_name": wind_name, "edge_index": ei,
                   "edge_id": edge_ids[ei], "source_1": a.source_id,
                   "source_2": b.source_id, "orientation": "x" if is_x[ei] else "y",
                   "dx_m": float(displacement[0]), "dy_m": float(displacement[1]),
                   "endpoint1_state": states[0], "midpoint_state": states[1],
                   "endpoint2_state": states[2], **f}
            if label in RESULT_KEYS:
                src = observed["winds"][RESULT_KEYS[label]]
                ea = float(src["A"]["energy"][ei])
                eb = float(src["B"]["energy"][ei])
                row.update({"energy_A": ea, "energy_B": eb,
                            "energy_split_mean": (ea + eb) / 2.0})
            else:
                row.update({"energy_A": None, "energy_B": None,
                            "energy_split_mean": None})
            rows.append(row)
        del sequence

    frame = pd.DataFrame(rows)
    assert len(frame) == 40 and len(wind_hashes) == 44
    np.save(out / "WCIG_R0_LOCAL_WIND_SAMPLES_4x10x11x3x3.npy",
            wind_samples, allow_pickle=False)
    frame.to_csv(out / "WCIG_R0_EDGE_WIND_PHYSICS.tsv", sep="\t", index=False)
    pd.DataFrame(wind_hashes).to_csv(
        out / "WCIG_R0_WIND_FILE_SHA256.tsv", sep="\t", index=False)

    features = frame[["A_parallel_mps", "A_perp_mps", "U_mps"]].to_numpy(float)
    target = frame["energy_split_mean"].to_numpy(float)[:30]
    avg = loow_loglinear(features[:30], target, is_x)
    split_a = loow_loglinear(features[:30],
                             frame["energy_A"].to_numpy(float)[:30], is_x)
    split_b = loow_loglinear(features[:30],
                             frame["energy_B"].to_numpy(float)[:30], is_x)
    ranks = loow_rank_only(features[:30], target)

    def screen(result: dict) -> dict:
        return {
            "pooled_ge_0p50": result["pooled_rho"] >= 0.50,
            "all_three_winds_positive": all(
                result["folds"][label]["rho"] > 0 for label in ("W0", "W1", "W2")),
            "orientation_reversal_predicted": result["predicted_family_reversal"],
        }

    primary = screen(avg)
    a_screen = screen(split_a)
    b_screen = screen(split_b)
    split_consistent = all(a_screen.values()) and all(b_screen.values())
    advance = all(primary.values()) and split_consistent

    all_beta = np.linalg.lstsq(design(features[:30]), np.log(target), rcond=None)[0]
    w3_pred = np.exp(design(features[30:]) @ all_beta)
    w3_order = np.argsort(w3_pred)
    w3_rows = []
    for ei, edge_id in enumerate(edge_ids):
        w3_rows.append({
            "edge_index": ei, "edge_id": edge_id,
            "orientation": "x" if is_x[ei] else "y",
            "predicted_energy": float(w3_pred[ei]),
            "predicted_rank_hard_to_easy": int(np.where(w3_order == ei)[0][0] + 1),
            "class": "HARD" if ei in w3_order[:3] else
                     ("EASY" if ei in w3_order[-3:] else "MIDDLE"),
        })
    pd.DataFrame(w3_rows).to_csv(
        out / "WCIG_R0_W3_PREOUTCOME_PREDICTION.tsv", sep="\t", index=False)
    similarities = {
        label: rho(w3_pred, target[wi * 10:(wi + 1) * 10])
        for wi, (label, _) in enumerate(WINDS[:3])
    }
    w3 = {
        "wind": "4,5-3_fast",
        "trained_on": ["W0", "W1", "W2"],
        "full_fit_coefficients": [float(v) for v in all_beta],
        "predicted_energy": [float(v) for v in w3_pred],
        "hard_edges": [edge_ids[i] for i in w3_order[:3]],
        "easy_edges": [edge_ids[i] for i in w3_order[-3:]],
        "x_vs_y": orientation(w3_pred, is_x),
        "similarity_rho_to_existing_energy": similarities,
        "w2_more_similar_than_w0_and_w1": bool(
            similarities["W2"] > max(similarities["W0"], similarities["W1"])),
        "no_w3_plume_outcomes_read": True,
    }
    result = {
        "state": "WCIG_R0_ADVANCE_TO_FRESH_WIND_PREDICTION" if advance
                 else "WCIG_R0_FAIL_STOP_WIND_GEOMETRY_MAINLINE",
        "scope": "zero_new_plume_simulations; W0/W1/W2 discovery physics audit",
        "N_environment_discovery": 3,
        "N_source": 8,
        "N_edge_per_environment": 10,
        "N_realization_new": 0,
        "physics_sample_rule": "GADEN validated nearest-cell map; (endpoint1+2*midpoint+endpoint2)/4; mean over 11 iterations",
        "model": "OLS log energy on log(A_parallel+1e-6), log(A_perp+1e-6), log(U+1e-6)",
        "inputs_sha256": {
            "inventory": EXPECTED["inventory"],
            "occupancy": EXPECTED["occupancy"],
            "lsc_result": EXPECTED["lsc_result"],
            "source_panel": EXPECTED["panel"],
        },
        "edge_ids": edge_ids,
        "split_averaged": avg,
        "split_A": split_a,
        "split_B": split_b,
        "rank_only_two_feature": ranks,
        "gates": {"primary": primary, "split_A": a_screen,
                  "split_B": b_screen, "split_consistency": split_consistent,
                  "advance": advance},
        "W3_preoutcome_prediction": w3,
    }
    (out / "WCIG_R0_RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n")
    lines = [
        "# WCIG R0 zero-plume decision",
        "",
        f"Decision: `{result['state']}`.",
        "The frozen LSC cross-wind D0 FAIL remains unchanged.",
        "",
        f"Pooled leave-one-wind-out rho: {avg['pooled_rho']:.6f}.",
        *[f"{label} held-out rho: {avg['folds'][label]['rho']:.6f}."
          for label in ("W0", "W1", "W2")],
        f"Wind-family orientation reversal predicted: {avg['predicted_family_reversal']}.",
        f"Split A/B screen consistency: {split_consistent}.",
        "",
        "W3 wind only was read; no W3 plume outcome was generated or scored.",
    ]
    (out / "WCIG_R0_DECISION.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "state": result["state"],
        "pooled_rho": avg["pooled_rho"],
        "heldout_rho": {k: avg["folds"][k]["rho"] for k in ("W0", "W1", "W2")},
        "orientation_reversal_predicted": avg["predicted_family_reversal"],
        "split_consistency": split_consistent,
        "W3_hard_edges": w3["hard_edges"],
        "W3_easy_edges": w3["easy_edges"],
    }, indent=2))


if __name__ == "__main__":
    main()
