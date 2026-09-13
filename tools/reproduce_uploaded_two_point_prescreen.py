#!/usr/bin/env python3
"""Reproduce the development-only route-pair screen when FEATURES.csv is supplied."""

import argparse
import itertools

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def source_ratio(values):
    values = values - values.mean(axis=0, keepdims=True)
    singular = np.linalg.svd(values, compute_uv=False)
    if len(singular) < 3 or singular[0] < 1e-12:
        return 0.0
    return float(singular[2] / singular[0])


def nearest_centroid(train_x, train_y, test_x):
    scaler = StandardScaler().fit(train_x)
    train_x = scaler.transform(train_x)
    test_x = scaler.transform(test_x)
    labels = sorted(set(train_y))
    centroids = {label: train_x[np.asarray(train_y) == label].mean(axis=0) for label in labels}
    return np.asarray([min(labels, key=lambda label: np.linalg.norm(row - centroids[label])) for row in test_x])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("features_csv")
    parser.add_argument("--out-prefix", default="two_point_virtual_prescreen")
    args = parser.parse_args()
    data = pd.read_csv(args.features_csv)
    feature_columns = [column for column in data.columns if len(column) > 1 and column[0] in "PRDUGW" and column[1:].isdigit()]
    sources = sorted(data.source.unique())
    winds = sorted(data.wind.unique())
    routes = sorted(data.route.unique())
    horizons = sorted(data.H.unique())
    standardized = data.copy()
    for horizon in horizons:
        mask = standardized.H == horizon
        scaler = StandardScaler().fit(standardized.loc[mask, feature_columns])
        standardized.loc[mask, feature_columns] = scaler.transform(standardized.loc[mask, feature_columns])
    vectors = {(row.route, row.wind, row.H, row.source): np.asarray([getattr(row, column) for column in feature_columns], dtype=float) for row in standardized.itertuples(index=False)}
    structural_rows = []
    for horizon in horizons:
        for wind in winds:
            for route_a, route_b in itertools.combinations(routes, 2):
                first = np.stack([vectors[(route_a, wind, horizon, source)] for source in sources])
                second = np.stack([vectors[(route_b, wind, horizon, source)] for source in sources])
                structural_rows.append({"H": horizon, "wind": wind, "route_a": route_a, "route_b": route_b, "best_single": max(source_ratio(first), source_ratio(second)), "ordinary_concat": source_ratio(np.c_[first, second]), "signed_diff": source_ratio(first - second)})
    structural = pd.DataFrame(structural_rows)
    structural.to_csv(args.out_prefix + "_structural.csv", index=False)
    raw_vectors = {(row.route, row.wind, row.H, row.source): np.asarray([getattr(row, column) for column in feature_columns], dtype=float) for row in data.itertuples(index=False)}
    accuracy_rows = []
    for horizon in horizons:
        for route_a, route_b in itertools.combinations(routes, 2):
            scores = {name: [] for name in ("single_a", "single_b", "concat", "diff")}
            for test_wind in winds:
                train_winds = [wind for wind in winds if wind != test_wind]
                train = {name: ([], []) for name in scores}
                test = {name: ([], []) for name in scores}
                for wind in train_winds:
                    for source in sources:
                        first = raw_vectors[(route_a, wind, horizon, source)]
                        second = raw_vectors[(route_b, wind, horizon, source)]
                        for name, value in {"single_a": first, "single_b": second, "concat": np.r_[first, second], "diff": first - second}.items():
                            train[name][0].append(value)
                            train[name][1].append(source)
                for source in sources:
                    first = raw_vectors[(route_a, test_wind, horizon, source)]
                    second = raw_vectors[(route_b, test_wind, horizon, source)]
                    for name, value in {"single_a": first, "single_b": second, "concat": np.r_[first, second], "diff": first - second}.items():
                        test[name][0].append(value)
                        test[name][1].append(source)
                for name in scores:
                    prediction = nearest_centroid(np.asarray(train[name][0]), np.asarray(train[name][1]), np.asarray(test[name][0]))
                    scores[name].extend(prediction == np.asarray(test[name][1]))
            accuracy_rows.append({"H": horizon, "route_a": route_a, "route_b": route_b, "best_single": max(np.mean(scores["single_a"]), np.mean(scores["single_b"])), "ordinary_concat": np.mean(scores["concat"]), "signed_diff": np.mean(scores["diff"])})
    accuracy = pd.DataFrame(accuracy_rows)
    accuracy.to_csv(args.out_prefix + "_leave_one_wind_accuracy.csv", index=False)
    print(structural.groupby("H")[["best_single", "ordinary_concat", "signed_diff"]].mean())
    print(accuracy.groupby("H")[["best_single", "ordinary_concat", "signed_diff"]].mean())


if __name__ == "__main__":
    main()
