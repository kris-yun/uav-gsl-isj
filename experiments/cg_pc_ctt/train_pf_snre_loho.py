#!/usr/bin/env python3
"""Manifest-driven LOHO trainer for the frozen PF-SNRE V2 topology."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
import time

import numpy as np
import torch
from torch.nn import functional as F

from pf_snre_final_core import (
    ConditionedMomentSetDirectNRE, HouseDataset, block_context,
    candidate_features, log_measurement, sha256,
)

TRAIN_TRAJECTORIES = tuple(range(10, 25))
VALIDATION_TRAJECTORIES = tuple(range(25, 30))


def load_manifest(path: Path) -> dict[str, HouseDataset]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("contract") != "PF_SNRE_MULTI_HOUSE_DATASET_V1":
        raise ValueError("wrong dataset manifest contract")
    base = path.parent
    houses = {}
    for house, s in spec.get("houses", {}).items():
        def p(key):
            v = Path(s[key])
            return v if v.is_absolute() else base / v
        houses[house] = HouseDataset.load(house, p("measured"), p("carriers"), p("blocks"))
    if set(houses) != {"H01", "H02", "H03"}:
        raise ValueError("manifest must contain exactly H01,H02,H03")
    for h, d in houses.items():
        if d.trajectory_count < 30:
            raise ValueError(f"{h}: need at least 30 canonical trajectories")
        for t in TRAIN_TRAJECTORIES + VALIDATION_TRAJECTORIES:
            if not np.any(d.blocks.update_visible_blocks[t] > 0):
                raise ValueError(f"{h}: trajectory {t} has no source-update prefix")
    return houses


@dataclass(frozen=True)
class Spec:
    house: str
    trajectory: int
    update: int
    source: int
    negative: int
    heldout: int


class BatchFactory:
    def __init__(self, houses: dict[str, HouseDataset], allowed: tuple[str, ...]):
        self.houses = houses
        self.allowed = tuple(allowed)
        if not self.allowed:
            raise ValueError("no training Houses")

    def sample_specs(self, pairs: int, trajectories: tuple[int, ...], rng: np.random.Generator):
        out = []
        for _ in range(pairs):
            house = self.allowed[int(rng.integers(0, len(self.allowed)))]
            d = self.houses[house]
            trajectory = int(trajectories[int(rng.integers(0, len(trajectories)))])
            available = np.flatnonzero(d.blocks.update_visible_blocks[trajectory] > 0) + 1
            update = int(available[int(rng.integers(0, len(available)))])
            source = int(rng.integers(0, d.source_count))
            # Independent product-of-marginals draw; equality with the positive
            # source is theoretically valid and is deliberately not rejected.
            negative = int(rng.integers(0, d.source_count))
            heldout = int(rng.integers(0, 8))
            out.append(Spec(house, trajectory, update, source, negative, heldout))
        return out

    def make_batch(self, specs: list[Spec]):
        max_blocks = max(self.houses[s.house].blocks.visible(s.trajectory, s.update) for s in specs)
        n = 2 * len(specs)
        obs_out = np.zeros((n, max_blocks, 10), np.float32)
        pred_out = np.zeros((n, max_blocks, 7, 10), np.float32)
        ctx_out = np.zeros((n, max_blocks, 6), np.float32)
        cand_out = np.zeros((n, 5), np.float32)
        block_mask = np.zeros((n, max_blocks), np.bool_)
        member_mask = np.ones((n, 7), np.bool_)
        labels = np.zeros(n, np.float32)
        for pair, s in enumerate(specs):
            d = self.houses[s.house]
            visible = d.blocks.visible(s.trajectory, s.update)
            idx = d.blocks.sample_indices[s.trajectory, :visible]
            observation = log_measurement(d.measured[s.source, s.heldout, s.trajectory][idx])
            members = np.asarray([m for m in range(8) if m != s.heldout], dtype=np.int64)
            if s.heldout in members or len(members) != 7:
                raise RuntimeError("strict 8->7 LOMO violated")
            for offset, (candidate, label) in enumerate(((s.source, 1.0), (s.negative, 0.0))):
                e = 2 * pair + offset
                pred = d.measured[candidate, members, s.trajectory][:, idx]
                pred = np.transpose(pred, (1, 0, 2))
                obs_out[e, :visible] = observation
                pred_out[e, :visible] = log_measurement(pred)
                ctx_out[e, :visible] = block_context(d, s.trajectory, visible, candidate)
                cand_out[e] = candidate_features(d.carriers[candidate], d.xy_center, d.xy_scale)
                block_mask[e, :visible] = True
                labels[e] = label
        return tuple(torch.from_numpy(x) for x in (
            obs_out, pred_out, ctx_out, cand_out, block_mask, member_mask, labels))


def evaluate_bce(model, factory, specs, device, chunk_pairs=16):
    model.eval()
    total = 0.0
    count = 0
    with torch.no_grad():
        for i in range(0, len(specs), chunk_pairs):
            batch = [x.to(device) for x in factory.make_batch(specs[i:i + chunk_pairs])]
            logits = model(*batch[:-1])
            label = batch[-1]
            total += float(F.binary_cross_entropy_with_logits(logits, label, reduction="sum"))
            count += int(label.numel())
    return total / count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-manifest", type=Path, required=True)
    ap.add_argument("--heldout-house", choices=("H01", "H02", "H03"), required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--steps", type=int, default=12000)
    ap.add_argument("--pairs-per-batch", type=int, default=8)
    ap.add_argument("--validation-pairs", type=int, default=256)
    ap.add_argument("--validation-every", type=int, default=250)
    args = ap.parse_args()
    if args.seed not in (3301, 3302, 3303):
        raise ValueError("only preregistered model seeds 3301/3302/3303 are allowed")
    if not 1 <= args.steps <= 12000:
        raise ValueError("steps must be in 1..12000")
    args.out.mkdir(parents=True, exist_ok=True)
    houses = load_manifest(args.dataset_manifest)
    allowed = tuple(h for h in ("H01", "H02", "H03") if h != args.heldout_house)
    factory = BatchFactory(houses, allowed)

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(min(4, max(1, torch.get_num_threads())))
    torch.use_deterministic_algorithms(True)
    device = torch.device("cpu")
    train_rng = np.random.default_rng(args.seed)
    val_rng = np.random.default_rng(args.seed + 1)
    val_specs = factory.sample_specs(args.validation_pairs, VALIDATION_TRAJECTORIES, val_rng)
    model = ConditionedMomentSetDirectNRE().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    initial = evaluate_bce(model, factory, val_specs, device)
    best = math.inf
    best_step = 0
    checkpoint = args.out / f"best_{args.heldout_house}_seed{args.seed}.pt"
    exposure = {h: np.zeros(houses[h].source_count, dtype=np.int64) for h in allowed}
    log_rows = []
    started = time.monotonic()
    for step in range(1, args.steps + 1):
        specs = factory.sample_specs(args.pairs_per_batch, TRAIN_TRAJECTORIES, train_rng)
        for s in specs:
            exposure[s.house][s.source] += 1
        batch = [x.to(device) for x in factory.make_batch(specs)]
        model.train()
        opt.zero_grad(set_to_none=True)
        logits = model(*batch[:-1])
        loss = F.binary_cross_entropy_with_logits(logits, batch[-1])
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        opt.step()
        if step == 1 or step % args.validation_every == 0 or step == args.steps:
            vb = evaluate_bce(model, factory, val_specs, device)
            row = {"step": step, "training_bce": float(loss.detach()), "validation_bce": vb,
                   "elapsed_s": time.monotonic() - started}
            log_rows.append(row)
            print("PF_SNRE_PROGRESS " + json.dumps(row, sort_keys=True), flush=True)
            if vb < best:
                best = vb
                best_step = step
                torch.save({
                    "model_state": model.state_dict(), "seed": args.seed, "step": step,
                    "validation_bce": vb,
                    "architecture": "conditioned_moment_set_direct_nre_v2_exact_topology",
                    "candidate_dim": 5, "block_context_dim": 6, "hidden": 32,
                    "heldout_house": args.heldout_house, "training_houses": allowed,
                }, checkpoint)
    if any(np.any(v == 0) for v in exposure.values()):
        raise RuntimeError("at least one source carrier had zero positive exposure")
    import csv
    with (args.out / "training_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(log_rows[0]))
        w.writeheader()
        w.writerows(log_rows)
    summary = {
        "contract": "PF_SNRE_LOHO_TRAIN_V1", "heldout_house": args.heldout_house,
        "training_houses": allowed, "seed": args.seed, "steps": args.steps,
        "train_trajectories": list(TRAIN_TRAJECTORIES),
        "validation_trajectories": list(VALIDATION_TRAJECTORIES),
        "initial_validation_bce": initial, "best_validation_bce": best, "best_step": best_step,
        "checkpoint_sha256": sha256(checkpoint),
        "dataset_manifest_sha256": sha256(args.dataset_manifest),
        "checkpoint_selection": "minimum simulated validation BCE only",
        "source_exposure": {h: {"min": int(v.min()), "median": float(np.median(v)), "max": int(v.max())}
                            for h, v in exposure.items()},
        "wall_time_s": time.monotonic() - started, "gaden_runs": 0,
    }
    (args.out / "training_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PF_SNRE_LOHO_TRAIN_COMPLETE " + json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
