#!/usr/bin/env python3
"""Run the frozen observability-learning baselines and mechanism controls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge


TARGET_NAMES = ("sigma3_sigma1", "q_energy", "log1p_min_pair_distance", "min_source_hit_support")
RICH = (0, 1, 2)
WINDOW = 26


def metric_report(y_true, y_pred, train_std):
    rows = []
    for index, name in enumerate(TARGET_NAMES):
        error = y_pred[:, index] - y_true[:, index]
        rmse = float(np.sqrt(np.mean(error * error)))
        if train_std[index] > 0:
            nrmse = float(rmse / train_std[index])
        else:
            nrmse = 0.0 if rmse == 0.0 else float("inf")
        true_std = float(np.std(y_true[:, index]))
        pred_std = float(np.std(y_pred[:, index]))
        corr = None if true_std == 0.0 or pred_std == 0.0 else float(np.corrcoef(y_true[:, index], y_pred[:, index])[0, 1])
        rows.append({"target": name, "rmse": rmse, "nrmse": nrmse, "pearson_r": corr})
    rich_score = float(np.mean([rows[index]["nrmse"] for index in RICH]))
    return {"per_target": rows, "rich_score_nrmse": rich_score}


def reverse_history(x, slices):
    out = x.copy()
    for first, last, width in slices:
        block = out[:, first:last].reshape(out.shape[0], width, -1)
        out[:, first:last] = block[:, ::-1, :].reshape(out.shape[0], last - first)
    return out


def model_fit_predict(x_train, y_train, x_eval, feature_count):
    x_train = x_train[:, :feature_count]
    x_eval = x_eval[:, :feature_count]
    mean = x_train.mean(axis=0)
    scale = x_train.std(axis=0)
    scale[scale == 0.0] = 1.0
    target_mean = y_train.mean(axis=0)
    target_scale = y_train.std(axis=0)
    target_scale[target_scale == 0.0] = 1.0
    x_train_z = (x_train - mean) / scale
    x_eval_z = (x_eval - mean) / scale
    y_train_z = (y_train - target_mean) / target_scale
    model = Ridge(alpha=1.0, fit_intercept=True, solver="cholesky")
    model.fit(x_train_z, y_train_z)
    prediction = model.predict(x_eval_z) * target_scale + target_mean
    return prediction


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--integrity", type=Path, required=True)
    parser.add_argument("--label-distribution", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    dataset = np.load(args.dataset, allow_pickle=False)
    x, y, metadata = dataset["X"], dataset["y"], dataset["metadata"]
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    integrity = json.loads(args.integrity.read_text(encoding="utf-8"))
    labels = json.loads(args.label_distribution.read_text(encoding="utf-8"))
    if integrity["status"] != "PASS" or labels["status"] != "PASS":
        raise RuntimeError("dataset integrity or label richness precondition failed")

    route = metadata[:, 0]
    wind = metadata[:, 1]
    train = (wind == "W_fast") & np.isin(route, np.asarray([f"AO_{i:02d}" for i in range(8)]))
    development = (wind == "W_fast") & np.isin(route, np.asarray([f"AO_{i:02d}" for i in range(8, 12)]))
    held = (wind == "W_slow") & np.isin(route, np.asarray([f"AO_{i:02d}" for i in range(8, 12)]))
    if (train.sum(), development.sum(), held.sum()) != (8 * 4 * 725, 4 * 4 * 725, 4 * 4 * 725):
        raise RuntimeError("frozen split cardinality failure")

    train_std = y[train].std(axis=0)
    model_features = {"gas_only": 2 * WINDOW, "gas_wind": 5 * WINDOW, "full": 11 * WINDOW}
    splits = {"train": train, "development": development, "held": held}
    results = {"schema": "OBSERVABILITY_LEARNING_FALSIFICATION_RESULTS_V1", "policy_schema": policy["schema"], "split_counts": {name: int(mask.sum()) for name, mask in splits.items()}, "models": {}, "controls": {}, "promotion_gate": policy["promotion_gate"]}
    predictions = {}
    for model_name, feature_count in model_features.items():
        predictions[model_name] = {}
        results["models"][model_name] = {}
        for split_name, mask in splits.items():
            if model_name == "gas_only" or model_name == "gas_wind" or model_name == "full":
                pred = model_fit_predict(x[train], y[train], x[mask], feature_count)
            predictions[model_name][split_name] = pred
            results["models"][model_name][split_name] = metric_report(y[mask], pred, train_std)

    constant_prediction = np.repeat(y[train].mean(axis=0)[None, :], int(held.sum()), axis=0)
    results["models"]["constant_train_mean"] = {"held": metric_report(y[held], constant_prediction, train_std)}
    control_slices = [(0, 2 * WINDOW, WINDOW), (2 * WINDOW, 5 * WINDOW, WINDOW), (5 * WINDOW, 8 * WINDOW, WINDOW), (8 * WINDOW, 11 * WINDOW, WINDOW)]
    held_x = x[held]
    dev_x = x[development]
    controls = {
        "time_reverse": (reverse_history(held_x, control_slices), reverse_history(dev_x, control_slices)),
        "wind_reverse": (reverse_history(held_x, [(2 * WINDOW, 5 * WINDOW, WINDOW)]), reverse_history(dev_x, [(2 * WINDOW, 5 * WINDOW, WINDOW)])),
        "motion_zero": (held_x.copy(), dev_x.copy()),
        "receiver_swap": (held_x.copy(), dev_x.copy()),
    }
    for name in ("motion_zero",):
        controls[name][0][:, 5 * WINDOW:11 * WINDOW] = 0.0
        controls[name][1][:, 5 * WINDOW:11 * WINDOW] = 0.0
    for name in ("receiver_swap",):
        for array in controls[name]:
            plus = array[:, :WINDOW].copy()
            array[:, :WINDOW] = array[:, WINDOW:2 * WINDOW]
            array[:, WINDOW:2 * WINDOW] = plus
    full_train = model_fit_predict(x[train], y[train], x[train], 11 * WINDOW)
    full_model = Ridge(alpha=1.0, fit_intercept=True, solver="cholesky")
    train_mean = x[train].mean(axis=0)
    train_scale = x[train].std(axis=0)
    train_scale[train_scale == 0.0] = 1.0
    target_mean = y[train].mean(axis=0)
    target_scale = y[train].std(axis=0)
    target_scale[target_scale == 0.0] = 1.0
    full_model.fit((x[train] - train_mean) / train_scale, (y[train] - target_mean) / target_scale)
    for name, (held_control, dev_control) in controls.items():
        held_prediction = full_model.predict((held_control - train_mean) / train_scale) * target_scale + target_mean
        dev_prediction = full_model.predict((dev_control - train_mean) / train_scale) * target_scale + target_mean
        results["controls"][name] = {"development": metric_report(y[development], dev_prediction, train_std), "held": metric_report(y[held], held_prediction, train_std)}

    full_held = results["models"]["full"]["held"]["rich_score_nrmse"]
    full_dev = results["models"]["full"]["development"]["rich_score_nrmse"]
    constant_held = results["models"]["constant_train_mean"]["held"]["rich_score_nrmse"]
    gas_only_held = results["models"]["gas_only"]["held"]["rich_score_nrmse"]
    constant_dev = metric_report(y[development], np.repeat(y[train].mean(axis=0)[None, :], int(development.sum()), axis=0), train_std)["rich_score_nrmse"]
    control_degradation = {name: results["controls"][name]["held"]["rich_score_nrmse"] / full_held - 1.0 if full_held > 0 else 0.0 for name in results["controls"]}
    gate = {
        "label_std_nonzero": bool(np.all(train_std[:3] > 0.0)),
        "held_vs_constant_improvement": float(1.0 - full_held / constant_held) if constant_held > 0 else 0.0,
        "held_vs_gas_only_improvement": float(1.0 - full_held / gas_only_held) if gas_only_held > 0 else 0.0,
        "development_vs_constant_improvement": float(1.0 - full_dev / constant_dev) if constant_dev > 0 else 0.0,
        "control_degradation": control_degradation,
        "receiver_swap_improvement": float(1.0 - results["controls"]["receiver_swap"]["held"]["rich_score_nrmse"] / full_held) if full_held > 0 else 0.0,
    }
    gate["conditions"] = {
        "label_std_nonzero": gate["label_std_nonzero"],
        "held_vs_constant": gate["held_vs_constant_improvement"] >= 0.20,
        "held_vs_gas_only": gate["held_vs_gas_only_improvement"] >= 0.10,
        "development_vs_constant": gate["development_vs_constant_improvement"] >= 0.20,
        "time_reverse_degradation": control_degradation["time_reverse"] >= 0.05,
        "wind_reverse_degradation": control_degradation["wind_reverse"] >= 0.05,
        "motion_zero_degradation": control_degradation["motion_zero"] >= 0.05,
        "receiver_swap_not_improved": gate["receiver_swap_improvement"] <= 0.05,
    }
    gate["all_conditions_pass"] = all(gate["conditions"].values())
    results["gate_metrics"] = gate
    results["OBSERVABILITY_AWARE_LEARNING_FALSIFICATION"] = "PASS" if gate["all_conditions_pass"] else "NO_GO"
    (args.out_dir / "FALSIFICATION_RESULTS.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    final_gate = {
        "schema": "OBSERVABILITY_LEARNING_FALSIFICATION_FINAL_GATE_V1",
        "DATASET_INTEGRITY": integrity["status"],
        "LABEL_DISTRIBUTION": labels["status"],
        "OBSERVABILITY_AWARE_LEARNING_FALSIFICATION": results["OBSERVABILITY_AWARE_LEARNING_FALSIFICATION"],
        "MAIN_INNOVATION_STATUS": "CANDIDATE_MAIN_INNOVATION_CONFIRMED_FOR_NEXT_STAGE" if gate["all_conditions_pass"] else "NOT_CONFIRMED",
        "MAIN_INNOVATION_CLAIM": "AUTHORIZED_FOR_INDEPENDENT_CONFIRMATION_ONLY" if gate["all_conditions_pass"] else "NOT_AUTHORIZED",
        "HELD_CONDITION": "W_slow_AO_08_AO_11",
        "NEW_GADEN": False,
        "W_ALTFAST_READ": False,
        "causal_localization_claim": "NOT_AUTHORIZED",
        "cross_dataset_claim": "NOT_AUTHORIZED",
    }
    (args.out_dir / "FINAL_GATE.json").write_text(json.dumps(final_gate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": results["OBSERVABILITY_AWARE_LEARNING_FALSIFICATION"], "gate": gate}))


if __name__ == "__main__":
    main()
