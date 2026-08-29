#!/usr/bin/env python3
"""Train one frozen H01 candidate-conditioned residual Set-NRE (seed 3101)."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import random
import time

import numpy as np
import torch
from torch.nn import functional as F

from pf_dei_set_nre import (
    ConditionedDeepSetNRE,
    block_context,
    build_block_layout,
    candidate_features,
    log_measurement,
    sha256,
)


SEED = 3101
TRAIN_TRAJECTORIES = tuple(range(25))
VALIDATION_TRAJECTORIES = tuple(range(25, 30))


class BatchFactory:
    def __init__(self, measured_path: Path, schedule_path: Path, carriers_path: Path,
                 posterior_path: Path, observed_block_manifest: Path):
        self.measured = np.load(measured_path, mmap_mode="r")
        schedule = np.load(schedule_path, allow_pickle=False)
        self.lengths = schedule["lengths"].astype(int)
        self.layouts = [
            build_block_layout(schedule["x"][i], schedule["y"][i],
                               schedule["stop_start"][i], int(self.lengths[i]))
            for i in range(30)
        ]
        authoritative = {seed: [] for seed in range(10)}
        with observed_block_manifest.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row["house"] == "House01" and int(row["seed"]) in authoritative:
                    authoritative[int(row["seed"])].append((
                        int(row["block_id"]),
                        np.asarray([int(v) for v in row["sample_row_indices"].split(";")], dtype=np.int64),
                    ))
        for seed in range(10):
            rows = sorted(authoritative[seed])
            if len(rows) < 128 or [r[0] for r in rows] != list(range(1, len(rows) + 1)):
                raise ValueError(f"seed{seed}: authoritative training blocks incomplete")
            layout = self.layouts[seed]
            indices = layout.sample_indices.copy()
            for block_id, values in rows:
                if block_id <= len(indices):
                    indices[block_id - 1] = values
            self.layouts[seed] = type(layout)(
                sample_indices=indices,
                stop_index=layout.stop_index,
                block_within_stop=layout.block_within_stop,
                stop_x=layout.stop_x,
                stop_y=layout.stop_y,
                available_updates=layout.available_updates,
            )
        self.carriers = json.loads(carriers_path.read_text(encoding="utf-8"))
        frozen = np.load(posterior_path, allow_pickle=False)
        self.q = np.asarray(frozen["posterior"], dtype=np.float64).reshape(50, 210)
        ids = np.asarray(frozen["carrier_id"]).astype(str)
        carrier_ids = np.asarray([c["carrier_id"] for c in self.carriers]).astype(str)
        if self.measured.shape[:3] != (210, 8, 30) or not np.array_equal(ids, carrier_ids):
            raise ValueError("training dataset/carrier/posterior identity mismatch")
        if np.any(self.q <= 0) or not np.allclose(self.q.sum(axis=1), 1.0, atol=1e-9):
            raise ValueError("PMFS posterior does not have strict normalized support")
        self.carrier_xy = np.asarray(
            [[c["centroid_x"], c["centroid_y"]] for c in self.carriers], dtype=np.float64)
        self.xy_center = 0.5 * (self.carrier_xy.min(axis=0) + self.carrier_xy.max(axis=0))
        self.xy_scale = np.maximum(self.carrier_xy.max(axis=0) - self.carrier_xy.min(axis=0), 1e-6)

    @staticmethod
    def categorical(q: np.ndarray, rng: np.random.Generator) -> int:
        return int(np.searchsorted(np.cumsum(q), rng.random(), side="right"))

    def sample_specs(self, pair_count: int, trajectories: tuple[int, ...],
                     rng: np.random.Generator):
        specs = []
        for _ in range(pair_count):
            trajectory = int(trajectories[int(rng.integers(0, len(trajectories)))])
            layout = self.layouts[trajectory]
            update = int(layout.available_updates[int(rng.integers(0, len(layout.available_updates)))])
            q_index = int(rng.integers(0, 50))
            q = self.q[q_index]
            source = self.categorical(q, rng)
            negative = self.categorical(q, rng)
            heldout = int(rng.integers(0, 8))
            specs.append((trajectory, update, q_index, source, negative, heldout))
        return specs

    def make_batch(self, specs):
        max_blocks = max(self.layouts[t].visible_blocks(u) for t, u, *_ in specs)
        examples = 2 * len(specs)
        obs_out = np.zeros((examples, max_blocks, 10), dtype=np.float32)
        pred_out = np.zeros((examples, max_blocks, 7, 10), dtype=np.float32)
        ctx_out = np.zeros((examples, max_blocks, 6), dtype=np.float32)
        cand_out = np.zeros((examples, 12), dtype=np.float32)
        block_mask = np.zeros((examples, max_blocks), dtype=np.bool_)
        member_mask = np.ones((examples, 7), dtype=np.bool_)
        labels = np.zeros(examples, dtype=np.float32)
        heldout_absent = True
        for pair, (trajectory, update, q_index, source, negative, heldout) in enumerate(specs):
            layout = self.layouts[trajectory]
            visible = layout.visible_blocks(update)
            indices = layout.sample_indices[:visible]
            observation = log_measurement(self.measured[source, heldout, trajectory][indices])
            prediction_members = np.asarray([m for m in range(8) if m != heldout], dtype=np.int64)
            heldout_absent &= heldout not in prediction_members
            for offset, (candidate, label) in enumerate(((source, 1.0), (negative, 0.0))):
                e = 2 * pair + offset
                pred = self.measured[candidate, prediction_members, trajectory][:, indices]
                pred = np.transpose(pred, (1, 0, 2))
                obs_out[e, :visible] = observation
                pred_out[e, :visible] = log_measurement(pred)
                ctx_out[e, :visible] = block_context(
                    layout, visible, self.carriers[candidate], self.xy_center, self.xy_scale)
                cand_out[e] = candidate_features(
                    self.carriers[candidate], self.xy_center, self.xy_scale,
                    self.q[q_index], self.carrier_xy, candidate)
                block_mask[e, :visible] = True
                labels[e] = label
        if not heldout_absent:
            raise ValueError("strict leave-one-member-out violated")
        return tuple(torch.from_numpy(x) for x in (
            obs_out, pred_out, ctx_out, cand_out, block_mask, member_mask, labels))


def evaluate_bce(model, factory: BatchFactory, specs, device, chunk_pairs: int = 16) -> float:
    model.eval()
    loss_sum = 0.0
    count = 0
    with torch.no_grad():
        for start in range(0, len(specs), chunk_pairs):
            batch = factory.make_batch(specs[start:start + chunk_pairs])
            obs, pred, ctx, cand, bmask, mmask, label = [x.to(device) for x in batch]
            logits = model(obs, pred, ctx, cand, bmask, mmask)
            loss_sum += float(F.binary_cross_entropy_with_logits(logits, label, reduction="sum"))
            count += int(label.numel())
    return loss_sum / count


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-root", type=Path, required=True)
    ap.add_argument("--pmfs-posteriors", type=Path, required=True)
    ap.add_argument("--observed-block-manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--steps", type=int, default=12000)
    ap.add_argument("--pairs-per-batch", type=int, default=8)
    ap.add_argument("--validation-pairs", type=int, default=128)
    ap.add_argument("--validation-every", type=int, default=250)
    args = ap.parse_args()
    if args.steps < 1 or args.steps > 12000:
        raise ValueError("training steps must be in 1..12000")
    args.out.mkdir(parents=True, exist_ok=True)

    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    torch.set_num_threads(min(4, max(1, torch.get_num_threads())))
    torch.use_deterministic_algorithms(True)
    device = torch.device("cpu")
    factory = BatchFactory(
        args.dataset_root / "H01_measured_train.npy",
        args.dataset_root / "H01_schedule_train.npz",
        args.dataset_root / "H01_carriers.json",
        args.pmfs_posteriors,
        args.observed_block_manifest,
    )
    train_rng = np.random.default_rng(SEED)
    val_rng = np.random.default_rng(SEED + 1)
    validation_specs = factory.sample_specs(args.validation_pairs, VALIDATION_TRAJECTORIES, val_rng)

    model = ConditionedDeepSetNRE().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    log_rows = []
    best_bce = math.inf
    best_step = 0
    checkpoint = args.out / "best_validation_bce_seed3101.pt"
    started = time.monotonic()
    initial_bce = evaluate_bce(model, factory, validation_specs, device)
    print(f"SET_NRE_INITIAL_VALIDATION_BCE={initial_bce:.9f}", flush=True)
    for step in range(1, args.steps + 1):
        model.train()
        specs = factory.sample_specs(args.pairs_per_batch, TRAIN_TRAJECTORIES, train_rng)
        batch = factory.make_batch(specs)
        obs, pred, ctx, cand, bmask, mmask, label = [x.to(device) for x in batch]
        optimizer.zero_grad(set_to_none=True)
        logits = model(obs, pred, ctx, cand, bmask, mmask)
        loss = F.binary_cross_entropy_with_logits(logits, label)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()

        if step == 1 or step % args.validation_every == 0 or step == args.steps:
            val_bce = evaluate_bce(model, factory, validation_specs, device)
            row = {
                "step": step,
                "training_bce": float(loss.detach()),
                "validation_bce": val_bce,
                "elapsed_s": time.monotonic() - started,
            }
            log_rows.append(row)
            print("SET_NRE_PROGRESS " + json.dumps(row, sort_keys=True), flush=True)
            # This is the only checkpoint selection rule.
            if val_bce < best_bce:
                best_bce = val_bce
                best_step = step
                torch.save({
                    "model_state": model.state_dict(),
                    "seed": SEED,
                    "step": step,
                    "validation_bce": val_bce,
                    "architecture": "candidate_conditioned_deep_set_plus_plus",
                    "candidate_dim": 12,
                    "block_context_dim": 6,
                    "hidden": 32,
                }, checkpoint)

    import csv
    with (args.out / "training_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(log_rows[0])); w.writeheader(); w.writerows(log_rows)
    summary = {
        "contract": "PF_DEI_CANDIDATE_CONDITIONED_RESIDUAL_SET_NRE_V1",
        "seed": SEED,
        "device": str(device),
        "steps_completed": args.steps,
        "maximum_steps": 12000,
        "pairs_per_batch": args.pairs_per_batch,
        "positive_source_sampling": "same empirical PMFS carrier posterior q as negative source",
        "negative_source_sampling": "independent categorical draw from empirical PMFS carrier posterior q",
        "class_balance": "one positive joint and one product-of-marginals negative per pseudo-observation",
        "strict_leave_one_member_out": True,
        "training_trajectories": list(TRAIN_TRAJECTORIES),
        "validation_trajectories": list(VALIDATION_TRAJECTORIES),
        "validation_pairs": args.validation_pairs,
        "checkpoint_selection": "minimum simulated validation BCE only",
        "initial_validation_bce": initial_bce,
        "best_validation_bce": best_bce,
        "best_step": best_step,
        "checkpoint_sha256": sha256(checkpoint),
        "dataset_summary_sha256": sha256(args.dataset_root / "H01_training_dataset_summary.json"),
        "pmfs_posterior_sha256": sha256(args.pmfs_posteriors),
        "observed_block_manifest_sha256": sha256(args.observed_block_manifest),
        "forbidden_architectures_used": [],
        "gaden_runs": 0,
        "wall_time_s": time.monotonic() - started,
    }
    (args.out / "training_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PF_DEI_SET_NRE_TRAINING_COMPLETE " + json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
