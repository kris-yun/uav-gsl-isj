#!/usr/bin/env python3
"""Offline M6 G1-C/G1-D gate on the frozen House02 compact bank.

This is deliberately a narrow, auditable offline probe.  It never starts ROS
or PMFS.  The learned arms use the same official 8-layer Transolver, the same
4->64->256 source adapter, optimizer, epochs, and source fractions.  The
scratch arm trains the complete randomly initialized Transolver and adapter
end to end.  The pretrained arm loads only the audited internal GeoPT tensors
and trains the adapter plus scalar task head.  Candidate rank is computed only
after each model is frozen.  The analytical kernel below is a labelled proxy
baseline; it is not the repaired Native PMFS simulator.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def import_g05(path: Path):
    spec = importlib.util.spec_from_file_location("g05_probe", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def parse_env_header(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()[:4]
    vals = [list(map(float, lines[0].split()[1:])), list(map(float, lines[1].split()[1:])),
            list(map(float, lines[2].split()[1:])), float(lines[3].split()[1])]
    return np.asarray(vals[0]), np.asarray(vals[1]), np.asarray(vals[2], dtype=int), float(vals[3])


def build_environment_features(grid_csv: Path, occupancy_path: Path, wind_path: Path):
    rows = []
    with grid_csv.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["occupancy"].strip() == "Free":
                rows.append(r)
    if len(rows) != 631:
        raise RuntimeError(f"expected 631 free grid rows, got {len(rows)}")
    xy = np.asarray([[float(r["x"]), float(r["y"])] for r in rows], dtype=np.float32)
    cell_idx = np.asarray([int(r["cell_index"]) for r in rows], dtype=np.int64)
    all_rows = list(csv.DictReader(grid_csv.open(newline="", encoding="utf-8")))
    obs = np.asarray([[float(r["x"]), float(r["y"])] for r in all_rows if r["occupancy"].strip() != "Free"], dtype=np.float32)
    # Pairwise nearest obstacle geometry is small (631 x 422), avoids an
    # unrecorded scipy dependency and is deterministic.
    dxy = xy[:, None, :] - obs[None, :, :]
    dsq = np.sum(dxy * dxy, axis=2)
    nearest = np.argmin(dsq, axis=1)
    dist = np.sqrt(dsq[np.arange(len(xy)), nearest])
    direction = dxy[np.arange(len(xy)), nearest] / np.maximum(dist[:, None], 1e-12)
    scale = 5.0 / (float(xy[:, 0].max() - xy[:, 0].min()) if len(xy) else 1.0)
    pos = np.column_stack(((xy[:, 0] - float(xy[:, 0].mean())) * scale,
                           (xy[:, 1] - float(xy[:, 1].min())) * scale,
                           np.zeros(len(xy), dtype=np.float32))).astype(np.float32)
    geom = np.column_stack((pos, dist * scale, direction[:, 0], direction[:, 1],
                            np.zeros(len(xy), dtype=np.float32)))
    env_min, _, dims, cell_size = parse_env_header(occupancy_path)
    n_cells = int(np.prod(dims))
    raw = np.fromfile(wind_path, dtype="<f8")
    if raw.size != 3 * n_cells:
        raise RuntimeError(f"legacy wind size mismatch: {raw.size} vs {3*n_cells}")
    wind = np.stack((raw[:n_cells], raw[n_cells:2*n_cells], raw[2*n_cells:]), axis=1)
    # GADEN index = ix + iy*nx + iz*nx*ny; use nearest sensor-plane cell.
    inds = np.floor((np.column_stack((xy, np.full(len(xy), 0.30))) - env_min) / cell_size).astype(int)
    if np.any(inds < 0) or np.any(inds[:, 0] >= dims[0]) or np.any(inds[:, 1] >= dims[1]) or np.any(inds[:, 2] >= dims[2]):
        raise RuntimeError("sensor point outside GADEN environment")
    wi = inds[:, 0] + inds[:, 1] * dims[0] + inds[:, 2] * dims[0] * dims[1]
    w = wind[wi].astype(np.float32)
    speed = np.linalg.norm(w, axis=1)
    unit = np.zeros_like(w)
    good = speed > 1e-12
    unit[good] = w[good] / speed[good, None]
    fx = np.column_stack((geom, unit, speed)).astype(np.float32)
    if fx.shape != (631, 11):
        raise RuntimeError(f"bad GeoPT feature shape {fx.shape}")
    return pos, fx, xy, cell_idx


def load_bank(bank: Path, splits, seeds):
    records = []
    order = {"train": 0, "val": 1, "test": 2}
    for source in sorted((p for p in bank.iterdir() if p.is_dir()), key=lambda p: (order.get(p.name.rstrip("0123456789"), 9), int("".join(c for c in p.name if c.isdigit()) or 0))):
        split = json.loads((source / f"seed{seeds[0]}" / "metadata.json").read_text())["split"]
        if split not in splits:
            continue
        meta0 = json.loads((source / f"seed{seeds[0]}" / "metadata.json").read_text())
        records.append({"id": source.name, "split": split, "xyz": np.asarray(meta0["source_xyz"], dtype=np.float32),
                        "cases": {seed: np.fromfile(source / f"seed{seed}" / "hit_frequency_f32.bin", dtype="<f4") for seed in seeds}})
    if not records:
        raise RuntimeError("no bank records")
    return records


class SourceArm:
    def __init__(self, torch, g05, official: Path, checkpoint: Path, pretrained: bool, seed: int, device):
        import torch.nn as nn
        self.torch = torch
        torch.manual_seed(seed); np.random.seed(seed); random.seed(seed)
        self.model, _ = g05.build_model(official, out_dim=1)
        if pretrained:
            ckpt = torch.load(checkpoint, map_location="cpu")
            state = self.model.state_dict()
            filtered = {k: v for k, v in ckpt.items() if k in state and tuple(v.shape) == tuple(state[k].shape)
                        and "mlp2" not in k and "ln_3" not in k}
            state.update(filtered); self.model.load_state_dict(state)
            self.loaded_keys = len(filtered)
        else:
            self.loaded_keys = 0
        self.model.to(device)
        if pretrained:
            # Keep the audited GeoPT representation frozen.  Only the scalar
            # task head and source adapter are fitted in this transfer arm.
            for p in self.model.parameters():
                p.requires_grad_(False)
            for name, p in self.model.blocks[-1].named_parameters():
                if name.startswith("ln_3") or name.startswith("mlp2"):
                    p.requires_grad_(True)
        else:
            # Scratch is a genuine same-architecture from-scratch control:
            # every Transolver and adapter parameter is trainable.
            for p in self.model.parameters():
                p.requires_grad_(True)
        self.adapter = nn.Sequential(nn.Linear(4, 64), nn.GELU(), nn.Linear(64, 256)).to(device)
        self.device = device
        self.params = [p for p in list(self.adapter.parameters()) + list(self.model.parameters()) if p.requires_grad]

    def __call__(self, pos, fx, source):
        t = self.torch
        b = source.shape[0]
        h = self.model.preprocess(t.cat((pos.expand(b, -1, -1), fx.expand(b, -1, -1)), dim=-1))
        h = h + self.model.placeholder[None, None, :]
        rel = pos.expand(b, -1, -1) - source[:, None, :]
        dist = t.linalg.vector_norm(rel, dim=-1, keepdim=True)
        h = h + self.adapter(t.cat((rel, dist), dim=-1))
        for block in self.model.blocks:
            h = block(h)
        return h.squeeze(-1)

    def state_dict(self):
        return {"model": self.model.state_dict(), "adapter": self.adapter.state_dict()}


def proxy_pmfs_field(pos, fx, source, torch):
    rel = pos[None, :, :] - source[:, None, :]
    u = fx[:, 7:10][None, :, :]
    speed = fx[:, 10][None, :]
    longitudinal = (rel * u).sum(-1)
    lateral = rel[..., 0] * (-u[..., 1]) + rel[..., 1] * u[..., 0]
    sig_minor = 1.0 / (1.0 + speed)
    sig_major = 1.0 + speed
    g = torch.exp(-0.5 * ((lateral / sig_minor) ** 2 + (longitudinal / sig_major) ** 2))
    return torch.clamp(0.3 + (0.6 - 0.3) * g, 1e-3, 0.999)


def metrics(pred, target, torch):
    p = torch.clamp(pred, 1e-5, 1 - 1e-5)
    return {"brier": float(torch.mean((p - target) ** 2).item()),
            "rmse": float(torch.sqrt(torch.mean((p - target) ** 2)).item()),
            "mae": float(torch.mean(torch.abs(p - target)).item()),
            "bce": float(torch.mean(-(target * torch.log(p) + (1 - target) * torch.log(1 - p))).item())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", type=Path, required=True)
    ap.add_argument("--grid", type=Path, required=True)
    ap.add_argument("--occupancy", type=Path, required=True)
    ap.add_argument("--wind", type=Path, required=True)
    ap.add_argument("--official", type=Path, required=True)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    import torch
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    g05 = import_g05(args.official.parent.parent / "research" / "geopt_physics_foundation_pmfs_v1" / "g0_5_runtime_probe.py") if False else None
    # The probe is copied beside this script on the execution host.
    probe_path = Path(__file__).with_name("g0_5_runtime_probe.py")
    if not probe_path.exists(): probe_path = args.official.parent / "g0_5_runtime_probe.py"
    g05 = import_g05(probe_path)
    g05.install_import_shims()
    pos_np, fx_np, xy_np, cell_idx = build_environment_features(args.grid, args.occupancy, args.wind)
    seeds = [2026092311, 2026092312]
    records = load_bank(args.bank, {"train", "val", "test"}, seeds)
    if args.smoke:
        records = [r for r in records if r["id"] in {"train1", "val1", "test1"}]
        train_ids, val_ids, test_ids, train_seeds, fractions, epochs = ["train1"], ["val1"], ["test1"], [seeds[0]], [1.0], min(args.epochs, 2)
    else:
        train_ids = [f"train{i}" for i in range(1, 9)]
        val_ids = ["val1", "val2"]; test_ids = ["test1", "test2"]
        train_seeds, fractions, epochs = seeds, [0.25, 0.5, 1.0], args.epochs
    by_id = {r["id"]: r for r in records}
    if any(i not in by_id for i in train_ids + val_ids + test_ids): raise RuntimeError("requested split missing")
    scale = 5.0 / (float(xy_np[:, 0].max() - xy_np[:, 0].min()))
    source_pos = {r["id"]: np.asarray([(r["xyz"][0] - xy_np[:, 0].mean()) * scale,
                                        (r["xyz"][1] - xy_np[:, 1].min()) * scale, 0.0], dtype=np.float32) for r in records}
    pos = torch.from_numpy(pos_np[None]).to(device); fx = torch.from_numpy(fx_np[None]).to(device)
    out = {"status": "SMOKE_ONLY" if args.smoke else "G1C_G1D_RUN", "device": str(device), "epochs": epochs,
           "optimizer": {"name": "Adam", "lr": 0.001}, "source_adapter": {"input": 4, "hidden": 64, "output": 256},
           "fractions": {}, "bank_sha256": sha256(args.grid), "checkpoint_sha256": sha256(args.checkpoint)}
    args.out.mkdir(parents=True, exist_ok=True)
    for frac in fractions:
        k = max(1, int(round(len(train_ids) * frac)))
        subset = train_ids[:k]
        fraction_key = str(frac)
        out["fractions"][fraction_key] = {"train_sources": subset, "arms": {}}
        # fixed sample list: source subset × predeclared plume seeds
        train_samples = [(sid, seed) for sid in subset for seed in train_seeds]
        for arm_name, pretrained in (("scratch", False), ("pretrained", True)):
            arm = SourceArm(torch, g05, args.official, args.checkpoint, pretrained, 20260923, device)
            opt = torch.optim.Adam(arm.params, lr=1e-3)
            targets = torch.from_numpy(np.stack([by_id[sid]["cases"][seed] for sid, seed in train_samples])).to(device)
            sources = torch.from_numpy(np.stack([source_pos[sid] for sid, _ in train_samples])).to(device)
            losses = []
            t0 = time.time()
            arm.model.train(); arm.adapter.train()
            for ep in range(epochs):
                opt.zero_grad(set_to_none=True)
                pred_logits = arm(pos, fx, sources)
                loss = torch.nn.functional.binary_cross_entropy_with_logits(pred_logits, targets)
                loss.backward(); opt.step(); losses.append(float(loss.item()))
            arm.model.eval(); arm.adapter.eval()
            val_targets = torch.from_numpy(np.stack([by_id[sid]["cases"][seeds[0]] for sid in val_ids])).to(device)
            val_sources = torch.from_numpy(np.stack([source_pos[sid] for sid in val_ids])).to(device)
            with torch.inference_mode():
                val_pred = torch.sigmoid(arm(pos, fx, val_sources))
            val_metrics = metrics(val_pred, val_targets, torch)
            # Freeze before any held-out test/rank query.
            for p in arm.params: p.requires_grad_(False)
            case_metrics = {}
            rank_cases = {}
            candidates = [source_pos[sid] for sid in train_ids + val_ids + test_ids]
            candidate_ids = train_ids + val_ids + test_ids
            cand_t = torch.from_numpy(np.stack(candidates)).to(device)
            with torch.inference_mode():
                cand_pred = torch.sigmoid(arm(pos, fx, cand_t))
                for sid in test_ids:
                    target = torch.from_numpy(by_id[sid]["cases"][seeds[1]]).to(device)
                    pred_truth = cand_pred[candidate_ids.index(sid)]
                    case_metrics[sid] = metrics(pred_truth, target, torch)
                    errors = torch.sqrt(torch.mean((cand_pred - target[None, :]) ** 2, dim=1))
                    order = torch.argsort(errors).cpu().tolist(); rank = order.index(candidate_ids.index(sid)) + 1
                    rank_cases[sid] = {"rank": rank, "candidate_count": len(candidate_ids), "top5": [candidate_ids[i] for i in order[:5]], "truth_rmse": float(errors[candidate_ids.index(sid)].item())}
            torch.save(arm.state_dict(), args.out / f"{arm_name}_frac{fraction_key.replace('.', '_')}.pt")
            out["fractions"][fraction_key]["arms"][arm_name] = {"train_samples": len(train_samples), "trainable_parameters": sum(p.numel() for p in arm.params),
                "final_train_bce": losses[-1], "loss_curve": losses, "seconds": time.time() - t0,
                "validation_seed": seeds[0], "validation": val_metrics, "test_independent_seed": seeds[1],
                "test_field": case_metrics, "truth_rank": rank_cases, "loaded_internal_keys": arm.loaded_keys}
        # Frozen analytical proxy is scored with identical candidates/targets.
        # It must not be described as current repaired Native PMFS: no ROS or
        # PMFS simulator is started in this offline gate.
        candidates = [source_pos[sid] for sid in train_ids + val_ids + test_ids]
        candidate_ids = train_ids + val_ids + test_ids
        cand_t = torch.from_numpy(np.stack(candidates)).to(device)
        with torch.inference_mode(): native = proxy_pmfs_field(pos, fx, cand_t, torch)
        native_cases = {}; native_ranks = {}
        for sid in test_ids:
            target = torch.from_numpy(by_id[sid]["cases"][seeds[1]]).to(device)
            errors = torch.sqrt(torch.mean((native - target[None, :]) ** 2, dim=1)); order = torch.argsort(errors).cpu().tolist(); truth_idx = candidate_ids.index(sid)
            native_cases[sid] = metrics(native[truth_idx], target, torch)
            native_ranks[sid] = {"rank": order.index(truth_idx) + 1, "candidate_count": len(candidate_ids), "top5": [candidate_ids[i] for i in order[:5]], "truth_rmse": float(errors[truth_idx].item())}
        out["fractions"][fraction_key]["arms"]["proxy_pmfs_kernel"] = {"test_field": native_cases, "truth_rank": native_ranks,
            "note": "offline analytical anisotropic PMFS-like proxy; not current Native PMFS simulator; no ROS/live loop"}
    (args.out / "g1c_g1d_results.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
