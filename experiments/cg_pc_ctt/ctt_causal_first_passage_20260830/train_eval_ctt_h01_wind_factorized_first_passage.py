#!/usr/bin/env python3
"""Frozen H01 wind-conditioned factorized first-passage M1 and offline gates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from torch import nn

from ctt_h01_wind_bank_io import (
    FIRST_PASSAGE_THRESHOLD_PPM,
    STOP_SAMPLES,
    first_passage,
    read_physical,
    read_wind,
    sensor_forward,
    sha256_file,
)


TRAIN_CONTEXTS = (0, 3, 5, 6, 8, 9)
VAL_CONTEXTS = (4, 7)
TEST_CONTEXTS = (1, 2)
TRAIN_MEMBERS = (0, 1, 2, 3, 4, 5)
VAL_MEMBERS = TRAIN_MEMBERS
TEST_MEMBERS = (6, 7)
TRAIN_ROUTES = (0, 1, 2)
VAL_ROUTES = (3,)
TEST_ROUTES = (4,)
ROUTE_SEEDS = (4001, 4002, 4003, 4004, 4005)
SEED = 20260835
BATCH = 2048
MAX_EPOCHS = 50
PATIENCE = 7
TOLERANCE = 1e-5
HIDDEN = 128
CLASSES = 81
WIND_START = 16
INPUT_DIM = 33
BOOTSTRAPS = 5000


def digest(text: str) -> bytes:
    return hashlib.sha256(text.encode("utf-8")).digest()


def load_carriers(path: Path) -> list[dict]:
    """Load the immutable PMFS quotient-carrier coordinates.

    These are candidate-region centroids, not any one nuisance placement from
    the 3-D physical generator.  Quadtree extent is encoded in the stable ID.
    """
    result = []
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    for row in rows:
        index = int(row["carrier_index"])
        carrier_id = row["carrier_id"]
        parts = carrier_id.split("_")
        if len(parts) != 5 or parts[0] != "quadtree":
            raise ValueError(f"CTT_H01_CARRIER_ID_FORMAT_FAIL:{carrier_id}")
        result.append({
            "index": index, "id": carrier_id,
            "x": float(row["x"]), "y": float(row["y"]),
            "size_i": float(parts[3]), "size_j": float(parts[4]),
        })
    result.sort(key=lambda item: item["index"])
    if len(result) != 210 or [row["index"] for row in result] != list(range(210)):
        raise ValueError("CTT_H01_CARRIER_CONTRACT_FAIL")
    if len({row["id"] for row in result}) != 210 or len({(row["x"], row["y"]) for row in result}) != 210:
        raise ValueError("CTT_H01_CARRIER_ALIAS_FAIL")
    return result


def load_schedule(path: Path) -> list[dict]:
    rows = []
    with path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            rows.append({
                "t": float(row["t_sim_s"]), "x": float(row["x"]), "y": float(row["y"]),
                "z": float(row["z"]), "yaw": float(row["yaw"]),
                "moving": int(row["is_moving"]), "stop": int(row["stop_id"]),
            })
    return rows


def stop_records(schedule: list[dict], wind: np.ndarray) -> list[dict]:
    if len(schedule) != len(wind):
        raise ValueError("CTT_H01_SCHEDULE_WIND_LENGTH_FAIL")
    xy = np.asarray([[row["x"], row["y"]] for row in schedule], dtype=np.float64)
    cumulative = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))])
    result = []
    previous = None
    for stop_id in sorted({row["stop"] for row in schedule}):
        indices = np.asarray([index for index, row in enumerate(schedule)
                              if row["stop"] == stop_id and row["moving"] == 0], dtype=np.int64)
        if len(indices) < STOP_SAMPLES:
            continue
        indices = indices[:STOP_SAMPLES]
        start, end = int(indices[0]), int(indices[-1]) + 1
        row = schedule[start]
        current = np.asarray([row["x"], row["y"]], dtype=np.float64)
        delta = np.zeros(2) if previous is None else current - previous
        current_wind = wind[indices]
        prefix_wind = wind[:end]
        route = np.asarray([
            row["t"], cumulative[start], delta[0], delta[1], math.sin(row["yaw"]), math.cos(row["yaw"]),
        ], dtype=np.float32)
        wind_features = np.concatenate([
            current_wind.mean(axis=0), current_wind.std(axis=0), current_wind[-1],
            prefix_wind.mean(axis=0), prefix_wind.std(axis=0),
        ]).astype(np.float32)
        result.append({"indices": indices, "xy": current, "route": route, "wind": wind_features})
        previous = current
    return result


def features(carrier: dict, stop: dict) -> np.ndarray:
    source = np.asarray([carrier["x"], carrier["y"]], dtype=np.float64)
    query = stop["xy"]
    delta = query - source
    distance = max(float(np.linalg.norm(delta)), 1e-6)
    unit = delta / distance
    half_diagonal = 0.5 * 0.3 * math.hypot(carrier["size_i"], carrier["size_j"])
    mean_wind = stop["wind"][:3]
    along = float(mean_wind[0] * unit[0] + mean_wind[1] * unit[1])
    cross = float(-mean_wind[0] * unit[1] + mean_wind[1] * unit[0])
    value = np.asarray([
        carrier["x"], carrier["y"], query[0], query[1], delta[0], delta[1], distance,
        unit[0], unit[1], half_diagonal, *stop["route"], *stop["wind"], along, cross,
    ], dtype=np.float32)
    if value.shape != (INPUT_DIM,) or not np.isfinite(value).all():
        raise ValueError(f"CTT_H01_FEATURE_CONTRACT_FAIL:{value.shape}")
    return value


class Factorized(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(INPUT_DIM, HIDDEN), nn.SiLU(), nn.Linear(HIDDEN, HIDDEN), nn.SiLU(),
            nn.Linear(HIDDEN, HIDDEN), nn.SiLU(),
        )
        self.survival = nn.Linear(HIDDEN, 1)
        self.phase = nn.Linear(HIDDEN, 80)

    def raw(self, values):
        hidden = self.encoder(values)
        return self.survival(hidden).squeeze(1), self.phase(hidden)

    def probabilities(self, values):
        survival, phase = self.raw(values)
        ever = torch.sigmoid(survival)
        conditional = torch.softmax(phase, dim=1)
        return torch.cat([ever[:, None] * conditional, (1.0 - ever)[:, None]], dim=1)


def factorized_loss(model, values, labels):
    survival, phase = model.raw(values)
    event = (labels < 80).float()
    survival_loss = nn.functional.binary_cross_entropy_with_logits(survival, event)
    mask = labels < 80
    phase_loss = nn.functional.cross_entropy(phase[mask], labels[mask]) if bool(mask.any()) else phase.sum() * 0.0
    return survival_loss + phase_loss, survival_loss, phase_loss


def make_stops(bank: Path, schedule_root: Path) -> tuple[list[list[dict]], list[list[dict]]]:
    schedules = [load_schedule(schedule_root / "H01" / "reserved" / f"trajectory_seed_{seed}.csv")
                 for seed in ROUTE_SEEDS]
    by_context = []
    for context in range(10):
        winds = read_wind(bank / f"context_{context:02d}" / "exact_wind_routes.bin")
        stops = [stop_records(schedule, wind) for schedule, wind in zip(schedules, winds)]
        if [len(items) for items in stops] != [10, 10, 10, 9, 10]:
            raise ValueError(f"CTT_H01_STOP_COUNT_FAIL:{context}:{[len(items) for items in stops]}")
        by_context.append(stops)
    return schedules, by_context


def build_examples(bank: Path, carriers: list[dict], stops, contexts, members, routes, capture_binary=False):
    x, y, clusters = [], [], []
    binary = {} if capture_binary else None
    for context in contexts:
        for carrier in carriers:
            for member in members:
                streams = read_physical(bank / f"context_{context:02d}" / f"member_{member:02d}" / f"{carrier['id']}.bin")
                for route in routes:
                    measured = sensor_forward(streams[route])
                    tape = []
                    for stop_index, stop in enumerate(stops[context][route]):
                        stop_measured = measured[stop["indices"]]
                        label = first_passage(stop_measured)
                        x.append(features(carrier, stop))
                        y.append(label)
                        clusters.append((context, carrier["index"], member, route, stop_index))
                        tape.append(stop_measured > FIRST_PASSAGE_THRESHOLD_PPM)
                    if capture_binary:
                        binary[(context, carrier["index"], member, route)] = np.asarray(tape, dtype=bool)
    return np.asarray(x, dtype=np.float32), np.asarray(y, dtype=np.int64), clusters, binary


def fit(name, x_train, y_train, x_val, y_val, mean, std, output: Path):
    train = ((x_train - mean) / std).astype(np.float32)
    validation = ((x_val - mean) / std).astype(np.float32)
    torch.manual_seed(SEED)
    model = Factorized()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-5)
    generator = torch.Generator().manual_seed(SEED)
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(torch.from_numpy(train), torch.from_numpy(y_train)),
        batch_size=BATCH, shuffle=True, generator=generator,
    )
    best = math.inf
    stale = 0
    history = []
    for epoch in range(MAX_EPOCHS):
        model.train(); total = survival_total = phase_total = count = 0
        for xb, yb in loader:
            loss, survival_loss, phase_loss = factorized_loss(model, xb, yb)
            optimizer.zero_grad(set_to_none=True); loss.backward(); optimizer.step()
            total += float(loss.detach()) * len(xb)
            survival_total += float(survival_loss.detach()) * len(xb)
            phase_total += float(phase_loss.detach()) * len(xb)
            count += len(xb)
        # The frozen validation objective is one global BCE plus one global
        # conditional-on-event CE.  Evaluate it as a single population rather
        # than averaging batch-local phase means with unequal hit fractions.
        model.eval()
        with torch.no_grad():
            validation_loss = float(factorized_loss(
                model, torch.from_numpy(validation), torch.from_numpy(y_val))[0])
        history.append({
            "epoch": epoch, "train_total": total / count,
            "train_survival": survival_total / count, "train_phase": phase_total / count,
            "validation_total": validation_loss,
        })
        print(f"CTT_H01_TRAIN arm={name} epoch={epoch} train={total/count:.8f} val={validation_loss:.8f}", flush=True)
        if validation_loss < best - TOLERANCE:
            best = validation_loss; stale = 0
            torch.save({
                "state": model.state_dict(), "mean": torch.from_numpy(mean), "std": torch.from_numpy(std),
                "epoch": epoch, "validation_loss": validation_loss,
            }, output / f"{name}_best.pt")
        else:
            stale += 1
            if stale >= PATIENCE:
                break
    (output / f"{name}_history.json").write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    checkpoint = torch.load(output / f"{name}_best.pt", weights_only=True)
    model.load_state_dict(checkpoint["state"])
    return model, checkpoint


def predict(model, checkpoint, values):
    normalized = ((values - checkpoint["mean"].numpy()) / checkpoint["std"].numpy()).astype(np.float32)
    chunks = []; model.eval()
    with torch.no_grad():
        for start in range(0, len(normalized), BATCH):
            chunks.append(model.probabilities(torch.from_numpy(normalized[start:start+BATCH])).numpy())
    return np.concatenate(chunks)


def proper_scores(probability, labels):
    clipped = np.clip(probability, 1e-12, 1.0)
    nll = -np.log(clipped[np.arange(len(labels)), labels])
    cdf = np.cumsum(probability[:, :80], axis=1)
    observed = (labels[:, None] <= np.arange(80)[None, :]).astype(np.float32)
    brier = ((cdf - observed) ** 2).mean(axis=1)
    return nll, brier


def cluster_mean(values, clusters):
    groups: dict[tuple[int, int], list[float]] = defaultdict(list)
    for value, cluster in zip(values, clusters):
        groups[(cluster[0], cluster[1])].append(float(value))
    return {key: float(np.mean(item)) for key, item in groups.items()}


def bootstrap(delta: dict[tuple[int, int], float]):
    values = np.asarray(list(delta.values()), dtype=np.float64)
    rng = np.random.default_rng(SEED)
    means = np.asarray([rng.choice(values, len(values), replace=True).mean() for _ in range(BOOTSTRAPS)])
    return float(values.mean()), [float(value) for value in np.quantile(means, [0.025, 0.975])]


def rank(score, truth):
    target = score[truth]
    return float(1 + np.count_nonzero(score > target) + 0.5 * (np.count_nonzero(score == target) - 1))


def sign_test(left, right):
    left = np.asarray(left); right = np.asarray(right)
    wins = int((left < right).sum()); losses = int((left > right).sum()); ties = int((left == right).sum())
    count = wins + losses
    p_value = (sum(math.comb(count, value) for value in range(wins, count + 1)) /
               (2 ** count)) if count else 1.0
    return {"wins": wins, "losses": losses, "ties": ties, "p": p_value}


def summarize(ranks):
    values = np.asarray(ranks, dtype=np.float64)
    return {
        "mean_normalized_rank": float(((values - 1) / 209).mean()),
        "median_rank": float(np.median(values)),
        "top5": float((values <= 5).mean()), "top10": float((values <= 10).mean()),
    }


def likelihood_parts(probability, labels):
    stop = np.arange(len(labels))
    full = np.log(np.clip(probability[:, stop, labels], 1e-12, 1.0)).sum(axis=1)
    ever_probability = 1.0 - probability[:, :, -1]
    event = labels < 80
    survival = np.where(
        event[None, :], np.log(np.clip(ever_probability, 1e-12, 1.0)),
        np.log(np.clip(1.0 - ever_probability, 1e-12, 1.0)),
    ).sum(axis=1)
    phase = np.zeros_like(ever_probability)
    for index in range(len(labels)):
        if event[index]:
            phase[:, index] = np.log(np.clip(
                probability[:, index, labels[index]] / np.clip(ever_probability[:, index], 1e-12, 1.0),
                1e-12, 1.0,
            ))
    return full, survival, phase.sum(axis=1)


def permuted_labels(binary, context, member, source):
    result = []
    for stop, tape in enumerate(binary):
        seed = int.from_bytes(digest(f"CTT-H01-WIND-M1-TIME|{context}|{member}|{source}|{stop}")[:8], "big")
        shuffled = tape[np.random.default_rng(seed).permutation(80)]
        result.append(int(np.argmax(shuffled)) if bool(shuffled.any()) else 80)
    return np.asarray(result, dtype=np.int64)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--schedule-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"REFUSE_OVERWRITE:{args.output}")
    summary = json.loads((args.bank / "bank_summary.json").read_text(encoding="utf-8"))
    if summary.get("verdict") != "CTT_H01_WIND_BANK_MATERIALIZATION_PASS" or not summary.get("scientific_gate_eligible"):
        raise SystemExit("CTT_H01_BANK_NOT_GATE_ELIGIBLE")
    args.output.mkdir(parents=True)
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED); torch.set_num_threads(4)
    carriers = load_carriers(args.support)
    _, stops = make_stops(args.bank, args.schedule_root)

    print("CTT_H01_BUILD_TRAIN", flush=True)
    x_train, y_train, train_clusters, _ = build_examples(
        args.bank, carriers, stops, TRAIN_CONTEXTS, TRAIN_MEMBERS, TRAIN_ROUTES)
    print("CTT_H01_BUILD_VALIDATION", flush=True)
    x_val, y_val, val_clusters, _ = build_examples(
        args.bank, carriers, stops, VAL_CONTEXTS, VAL_MEMBERS, VAL_ROUTES)
    mean = x_train.mean(axis=0); std = x_train.std(axis=0); std[std < 1e-6] = 1.0
    x_train_static = x_train.copy(); x_train_static[:, WIND_START:] = mean[WIND_START:]
    x_val_static = x_val.copy(); x_val_static[:, WIND_START:] = mean[WIND_START:]
    contract = {
        "contract": "CTT_H01_WIND_FACTORIZED_FIRST_PASSAGE_GATE_V1",
        "bank_sha256": sha256_file(args.bank / "bank_summary.json"),
        "split": {"train_contexts": TRAIN_CONTEXTS, "validation_contexts": VAL_CONTEXTS,
                  "test_contexts": TEST_CONTEXTS, "train_members": TRAIN_MEMBERS,
                  "test_members": TEST_MEMBERS, "train_routes": [4001, 4002, 4003],
                  "validation_route": 4004, "test_route": 4005},
        "input_dim": INPUT_DIM, "seed": SEED, "hidden": [128, 128, 128],
        "loss": "BCE_ever_plus_CE_phase_given_ever_unit_weights", "batch": BATCH,
        "max_epochs": MAX_EPOCHS, "patience": PATIENCE, "test_opened": False,
    }
    (args.output / "06_TRAINING_CONTRACT.json").write_text(json.dumps(contract, indent=2) + "\n")
    conditional, conditional_checkpoint = fit("conditional", x_train, y_train, x_val, y_val, mean, std, args.output)
    static, static_checkpoint = fit("static", x_train_static, y_train, x_val_static, y_val, mean, std, args.output)
    contract["test_opened"] = True
    contract["checkpoints"] = {
        "conditional": sha256_file(args.output / "conditional_best.pt"),
        "static": sha256_file(args.output / "static_best.pt"),
    }
    (args.output / "06_TRAINING_CONTRACT.json").write_text(json.dumps(contract, indent=2) + "\n")

    print("CTT_H01_BUILD_TEST_AFTER_CHECKPOINT_FREEZE", flush=True)
    x_test, y_test, test_clusters, test_binary = build_examples(
        args.bank, carriers, stops, TEST_CONTEXTS, TEST_MEMBERS, TEST_ROUTES, capture_binary=True)
    x_test_static = x_test.copy(); x_test_static[:, WIND_START:] = mean[WIND_START:]
    p_conditional = predict(conditional, conditional_checkpoint, x_test)
    p_static = predict(static, static_checkpoint, x_test_static)
    repeat_error = float(np.max(np.abs(p_conditional - predict(conditional, conditional_checkpoint, x_test))))
    normalization = float(np.max(np.abs(p_conditional.sum(axis=1) - 1.0)))
    cond_nll, cond_brier = proper_scores(p_conditional, y_test)
    static_nll, static_brier = proper_scores(p_static, y_test)
    c_nll = cluster_mean(cond_nll, test_clusters); s_nll = cluster_mean(static_nll, test_clusters)
    c_brier = cluster_mean(cond_brier, test_clusters); s_brier = cluster_mean(static_brier, test_clusters)
    delta_nll = {key: s_nll[key] - c_nll[key] for key in c_nll}
    delta_brier = {key: s_brier[key] - c_brier[key] for key in c_brier}
    mean_nll, ci_nll = bootstrap(delta_nll); mean_brier, ci_brier = bootstrap(delta_brier)

    # Matched context swap: context 1 receives context 2 features and vice versa.
    x_shuffle = x_test.copy()
    lookup = {cluster: index for index, cluster in enumerate(test_clusters)}
    for index, cluster in enumerate(test_clusters):
        other = (3 - cluster[0], *cluster[1:])
        x_shuffle[index, WIND_START:] = x_test[lookup[other], WIND_START:]
    p_shuffle = predict(conditional, conditional_checkpoint, x_shuffle)
    shuffle_nll, _ = proper_scores(p_shuffle, y_test)
    shuffled_cluster = cluster_mean(shuffle_nll, test_clusters)
    shuffle_delta = {key: shuffled_cluster[key] - c_nll[key] for key in c_nll}
    shuffle_mean, shuffle_ci = bootstrap(shuffle_delta)
    per_context = {}
    for context in TEST_CONTEXTS:
        mask = np.asarray([cluster[0] == context for cluster in test_clusters])
        per_context[str(context)] = {
            "conditional_nll": float(cond_nll[mask].mean()), "static_nll": float(static_nll[mask].mean()),
            "conditional_brier": float(cond_brier[mask].mean()), "static_brier": float(static_brier[mask].mean()),
        }
    physical_gate = {
        "static_minus_conditional_nll_ci_lower_positive": ci_nll[0] > 0,
        "static_minus_conditional_brier_ci_lower_positive": ci_brier[0] > 0,
        "conditional_better_both_scores_context_1": per_context["1"]["conditional_nll"] < per_context["1"]["static_nll"] and per_context["1"]["conditional_brier"] < per_context["1"]["static_brier"],
        "conditional_better_both_scores_context_2": per_context["2"]["conditional_nll"] < per_context["2"]["static_nll"] and per_context["2"]["conditional_brier"] < per_context["2"]["static_brier"],
        "matched_context_shuffle_hurts_nll": shuffle_ci[0] > 0,
        "normalization": normalization < 1e-6,
        "repeat_determinism": repeat_error == 0.0,
        "all_queries_in_frozen_support": len(carriers) == 210,
    }
    physical_report = {
        "contract": contract["contract"], "examples": len(y_test), "per_context": per_context,
        "static_minus_conditional_nll": mean_nll, "nll_95ci": ci_nll,
        "static_minus_conditional_brier": mean_brier, "brier_95ci": ci_brier,
        "matched_context_shuffle_minus_conditional_nll": shuffle_mean,
        "shuffle_nll_95ci": shuffle_ci, "normalization_error": normalization,
        "repeat_max_abs": repeat_error, "gate": physical_gate,
        "verdict": "CTT_H01_WIND_CONDITIONED_NEURAL_M1_PHYSICAL_PASS" if all(physical_gate.values()) else "CTT_H01_WIND_CONDITIONED_NEURAL_M1_PHYSICAL_NO_GO",
    }
    (args.output / "07_M1_PHYSICAL_GATE.json").write_text(json.dumps(physical_report, indent=2) + "\n")
    if not all(physical_gate.values()):
        (args.output / "VERDICT.txt").write_text(physical_report["verdict"] + "\n")
        print(json.dumps(physical_report, indent=2)); return 2

    # Candidate probabilities are member-invariant because member is marginalized by training.
    candidate_conditional = {}; candidate_static = {}
    for context in TEST_CONTEXTS:
        for source in range(210):
            indices = [lookup[(context, source, TEST_MEMBERS[0], TEST_ROUTES[0], stop)] for stop in range(10)]
            candidate_conditional[(context, source)] = p_conditional[indices]
            candidate_static[(context, source)] = p_static[indices]
    rows = []
    for context in TEST_CONTEXTS:
        probabilities = np.stack([candidate_conditional[(context, source)] for source in range(210)])
        static_probabilities = np.stack([candidate_static[(context, source)] for source in range(210)])
        for member in TEST_MEMBERS:
            permutation_seed = int.from_bytes(digest(f"CTT-H01-WIND-M1-PHASE|{context}|{member}")[:8], "big")
            phase_permutation = np.random.default_rng(permutation_seed).permutation(210)
            for truth in range(210):
                key = (context, truth, member, TEST_ROUTES[0])
                tape = test_binary[key]
                labels = np.asarray([int(np.argmax(row)) if bool(row.any()) else 80 for row in tape])
                full, survival, phase = likelihood_parts(probabilities, labels)
                static_full, _, _ = likelihood_parts(static_probabilities, labels)
                permuted = permuted_labels(tape, context, member, truth)
                time_full, _, _ = likelihood_parts(probabilities, permuted)
                phase_shuffle = survival + phase[phase_permutation]
                rows.append({
                    "context": context, "member": member, "truth": truth,
                    "carrier_id": carriers[truth]["id"],
                    "rank_full": rank(full, truth), "rank_survival": rank(survival, truth),
                    "rank_time_permute": rank(time_full, truth),
                    "rank_phase_label_shuffle": rank(phase_shuffle, truth),
                    "rank_static_wind_full": rank(static_full, truth),
                })
    with (args.output / "08_SOURCE_EVIDENCE_CASES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    keys = ("rank_full", "rank_survival", "rank_time_permute", "rank_phase_label_shuffle", "rank_static_wind_full")
    arrays = {key: np.asarray([row[key] for row in rows]) for key in keys}
    summaries = {key: summarize(value) for key, value in arrays.items()}
    comparisons = {
        "full_vs_survival": sign_test(arrays["rank_full"], arrays["rank_survival"]),
        "full_vs_time_permute": sign_test(arrays["rank_full"], arrays["rank_time_permute"]),
        "full_vs_phase_label_shuffle": sign_test(arrays["rank_full"], arrays["rank_phase_label_shuffle"]),
        "full_vs_static_wind": sign_test(arrays["rank_full"], arrays["rank_static_wind_full"]),
    }
    context_direction = {}
    for context in TEST_CONTEXTS:
        mask = np.asarray([row["context"] == context for row in rows])
        context_direction[str(context)] = {
            "full_minus_survival_mean_rank": float(arrays["rank_full"][mask].mean() - arrays["rank_survival"][mask].mean()),
            "full_minus_time_permute_mean_rank": float(arrays["rank_full"][mask].mean() - arrays["rank_time_permute"][mask].mean()),
        }
    source_gate = {
        "full_beats_survival": summaries["rank_full"]["mean_normalized_rank"] < summaries["rank_survival"]["mean_normalized_rank"] and comparisons["full_vs_survival"]["p"] <= 0.01,
        "full_top10_non_degrade_survival": summaries["rank_full"]["top10"] >= summaries["rank_survival"]["top10"],
        "full_beats_time_permute": summaries["rank_full"]["mean_normalized_rank"] < summaries["rank_time_permute"]["mean_normalized_rank"] and comparisons["full_vs_time_permute"]["p"] <= 0.01,
        "full_beats_phase_label_shuffle": summaries["rank_full"]["mean_normalized_rank"] < summaries["rank_phase_label_shuffle"]["mean_normalized_rank"] and comparisons["full_vs_phase_label_shuffle"]["p"] <= 0.01,
        "full_beats_static_wind": summaries["rank_full"]["mean_normalized_rank"] < summaries["rank_static_wind_full"]["mean_normalized_rank"] and comparisons["full_vs_static_wind"]["p"] <= 0.01,
        "nonnegative_direction_each_context": all(
            value["full_minus_survival_mean_rank"] <= 0 and value["full_minus_time_permute_mean_rank"] <= 0
            for value in context_direction.values()),
    }
    source_report = {
        "contract": "CTT_H01_WIND_CONDITIONED_FIRST_PASSAGE_SOURCE_EVIDENCE_V1",
        "case_count": len(rows), "summary": summaries, "comparisons": comparisons,
        "per_context_direction": context_direction, "gate": source_gate,
        "verdict": "CTT_H01_WIND_CONDITIONED_FIRST_PASSAGE_SOURCE_EVIDENCE_PASS" if all(source_gate.values()) else "CTT_H01_WIND_CONDITIONED_FIRST_PASSAGE_SOURCE_EVIDENCE_NO_GO",
    }
    (args.output / "08_SOURCE_EVIDENCE_GATE.json").write_text(json.dumps(source_report, indent=2) + "\n")
    (args.output / "VERDICT.txt").write_text(source_report["verdict"] + "\n")
    print(json.dumps({"physical": physical_report, "source": source_report}, indent=2))
    return 0 if all(source_gate.values()) else 3


if __name__ == "__main__":
    raise SystemExit(main())
