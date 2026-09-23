#!/usr/bin/env python3
"""Frozen House02 C0.5 diagnostic v2; source sign repair before holdout."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


TRAIN_CELLS = ("S1_W1_A", "S1_W1_B", "S2_W1_A", "S2_W1_B", "S1_W2_A", "S1_W2_B")
HOLDOUT_CELLS = ("S2_W2_A", "S2_W2_B")
TIMES = (100, 150, 200, 250, 300, 350, 400, 450, 500, 550)
TRAIN_SEEDS = (1729, 2718)
EPOCHS = 80
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-5
BATCH_SIZE = 10
WIDTH = 8
DILATIONS = (1, 2, 4, 8, 16)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


class TransportStep(nn.Module):
    def __init__(self, width: int, dilation: int):
        super().__init__()
        self.state = nn.Conv2d(width, width, 3, padding=dilation, dilation=dilation, bias=False)
        self.gate = nn.Conv2d(5, width, 1)

    def forward(self, state: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        move = F.relu(self.state(state)) * torch.sigmoid(self.gate(context))
        return F.relu(state + move) * (1.0 - context[:, 3:4])


class OperatorModel(nn.Module):
    """Source field is injected first; transport steps see wind, mask, time."""

    def __init__(self):
        super().__init__()
        self.injection = nn.Conv2d(1, WIDTH, 1, bias=False)
        self.transport = nn.ModuleList(TransportStep(WIDTH, d) for d in DILATIONS)
        self.readout = nn.Conv2d(WIDTH, 1, 1, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Source maps are nonnegative impulses. An all-negative 1x1 initialization
        # is killed by ReLU and receives zero gradient. Magnitude preserves a
        # nonnegative, source-supported injection without a trainable offset.
        state = torch.abs(self.injection(x[:, :1]))
        context = x[:, 1:]
        for step in self.transport:
            state = step(state, context)
        return self.readout(state) * (1.0 - context[:, 3:4])


class MonolithicModel(nn.Module):
    """Entangled source, wind, mask, and time input with matched capacity."""

    def __init__(self):
        super().__init__()
        self.layers = nn.ModuleList()
        for i, d in enumerate(DILATIONS):
            self.layers.append(nn.Conv2d(6 if i == 0 else WIDTH, WIDTH, 3,
                                         padding=d, dilation=d))
        self.extra = nn.Conv2d(WIDTH, WIDTH, 1)
        self.readout = nn.Conv2d(WIDTH, 1, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        state = x
        for layer in self.layers:
            state = F.relu(layer(state))
        state = F.relu(self.extra(state))
        return self.readout(state) * (1.0 - x[:, 4:5])


def parameter_count(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def context(root: Path) -> dict[str, np.ndarray]:
    folder = root / "context"
    source = {s: np.load(folder / f"source_map_{s}.npy", allow_pickle=False).astype(np.float32)
              for s in ("S1", "S2")}
    winds = {w: np.load(folder / f"wind_{w}_z0p20.npy", allow_pickle=False).astype(np.float32)
             for w in ("W1", "W2")}
    mask = np.load(folder / "obstacle_mask_z0p20.npy", allow_pickle=False)
    if mask.shape != (83, 119) or not all(a.shape == (83, 119) for a in source.values()):
        raise ValueError("source or mask shape drift")
    if not all(a.shape == (83, 119, 3) for a in winds.values()):
        raise ValueError("wind shape drift")
    return {"source": source, "wind": winds, "mask": (mask > 0).astype(np.float32)}


def make_data(root: Path, cells: tuple[str, ...]) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
    ctx = context(root)
    features: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    labels: list[str] = []
    for cell in cells:
        source_id, wind_id, _ = cell.split("_")
        path = root / cell / "spatial" / "concentration.npy"
        field = np.load(path, allow_pickle=False)
        if field.shape != (10, 83, 119) or not np.isfinite(field).all() or (field < 0).any():
            raise ValueError(f"concentration contract drift: {cell}")
        for i, time_step in enumerate(TIMES):
            source = ctx["source"][source_id]
            wind = ctx["wind"][wind_id]
            mask = ctx["mask"]
            time = np.full_like(source, time_step / 550.0)
            x = np.concatenate((source[None], wind.transpose(2, 0, 1), mask[None], time[None]))
            features.append(x)
            targets.append(np.log1p(field[i])[None])
            labels.append(f"{cell}:{time_step}")
    x = torch.from_numpy(np.stack(features))
    y = torch.from_numpy(np.stack(targets))
    # Fixed 2x reduction; no target-fitted spatial transform.
    x_source = F.max_pool2d(x[:, :1], 2, ceil_mode=True)
    x_wind = F.avg_pool2d(x[:, 1:4], 2, ceil_mode=True)
    x_mask = F.max_pool2d(x[:, 4:5], 2, ceil_mode=True)
    x_time = F.avg_pool2d(x[:, 5:6], 2, ceil_mode=True)
    x = torch.cat((x_source, x_wind, x_mask, x_time), dim=1)
    y = F.avg_pool2d(y, 2, ceil_mode=True)
    return x, y, labels


def train(root: Path, output: Path) -> None:
    torch.set_num_threads(4)
    mono_params = parameter_count(MonolithicModel())
    op_params = parameter_count(OperatorModel())
    if abs(mono_params - op_params) / max(mono_params, op_params) > 0.1:
        raise ValueError(f"parameter mismatch: monolithic={mono_params}, operator={op_params}")
    x, y, labels = make_data(root, TRAIN_CELLS)
    output.mkdir(parents=True, exist_ok=False)
    results = {"train_cells": TRAIN_CELLS, "holdout_cells_unopened": HOLDOUT_CELLS,
               "train_seeds": TRAIN_SEEDS, "epochs": EPOCHS, "learning_rate": LEARNING_RATE,
               "weight_decay": WEIGHT_DECAY, "batch_size": BATCH_SIZE,
               "parameter_counts": {"monolithic": mono_params, "operator": op_params},
               "train_labels": labels, "fits": {}}
    for kind, constructor in (("monolithic", MonolithicModel), ("operator", OperatorModel)):
        for seed in TRAIN_SEEDS:
            torch.manual_seed(seed)
            model = constructor()
            optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE,
                                         weight_decay=WEIGHT_DECAY)
            rng = np.random.default_rng(seed)
            losses = []
            for epoch in range(EPOCHS):
                indices = rng.permutation(len(x))
                epoch_losses = []
                model.train()
                for start in range(0, len(x), BATCH_SIZE):
                    batch = indices[start:start + BATCH_SIZE]
                    prediction = model(x[batch])
                    free = 1.0 - x[batch, 4:5]
                    loss = (((prediction - y[batch]) ** 2) * free).sum() / free.sum()
                    optimizer.zero_grad(set_to_none=True)
                    loss.backward()
                    optimizer.step()
                    epoch_losses.append(float(loss.detach()))
                losses.append(float(np.mean(epoch_losses)))
            checkpoint = output / f"{kind}_seed{seed}.pt"
            torch.save(model.state_dict(), checkpoint)
            results["fits"][f"{kind}_seed{seed}"] = {
                "training_loss_first": losses[0], "training_loss_last": losses[-1],
                "checkpoint_sha256": file_sha256(checkpoint)}
            print(f"{kind} seed={seed} loss={losses[-1]:.6g}", flush=True)
    (output / "train_manifest.json").write_text(json.dumps(results, indent=2) + "\n")


def evaluate(root: Path, output: Path) -> None:
    torch.set_num_threads(4)
    manifest = json.loads((output / "train_manifest.json").read_text())
    if tuple(manifest["train_cells"]) != TRAIN_CELLS:
        raise ValueError("training split drift")
    x, y, labels = make_data(root, HOLDOUT_CELLS)
    results = {"holdout_cells": HOLDOUT_CELLS, "labels": labels, "fits": {}}
    with torch.no_grad():
        for kind, constructor in (("monolithic", MonolithicModel), ("operator", OperatorModel)):
            for seed in TRAIN_SEEDS:
                checkpoint = output / f"{kind}_seed{seed}.pt"
                if file_sha256(checkpoint) != manifest["fits"][f"{kind}_seed{seed}"]["checkpoint_sha256"]:
                    raise ValueError("checkpoint hash drift")
                model = constructor()
                model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True))
                model.eval()
                prediction = model(x)
                free = 1.0 - x[:, 4:5]
                by_cell = {}
                for i, cell in enumerate(HOLDOUT_CELLS):
                    span = slice(i * 10, (i + 1) * 10)
                    error = (((prediction[span] - y[span]) ** 2) * free[span]).sum() / free[span].sum()
                    by_cell[cell] = float(error)
                results["fits"][f"{kind}_seed{seed}"] = by_cell
    (output / "heldout_field_result.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results["fits"], indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate"))
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.mode == "train":
        train(args.root, args.output)
    else:
        evaluate(args.root, args.output)


if __name__ == "__main__":
    main()
