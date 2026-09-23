#!/usr/bin/env python3
"""Geometry-selected sparse source-rank diagnostic on frozen C0.5 models."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F


def load_model_module(path: Path):
    spec = importlib.util.spec_from_file_location("c05_frozen_model", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def inputs(module, root: Path, source_id: str, wind_id: str) -> torch.Tensor:
    ctx = module.context(root)
    source = ctx["source"][source_id]
    wind = ctx["wind"][wind_id]
    mask = ctx["mask"]
    items = []
    for step in module.TIMES:
        time = np.full_like(source, step / 550.0)
        items.append(np.concatenate((source[None], wind.transpose(2, 0, 1),
                                     mask[None], time[None])))
    x = torch.from_numpy(np.stack(items))
    return torch.cat((F.max_pool2d(x[:, :1], 2, ceil_mode=True),
                      F.avg_pool2d(x[:, 1:4], 2, ceil_mode=True),
                      F.max_pool2d(x[:, 4:5], 2, ceil_mode=True),
                      F.avg_pool2d(x[:, 5:6], 2, ceil_mode=True)), dim=1)


def probe_points(mask: np.ndarray) -> list[list[int]]:
    """One closest free cell per 5x6 equal-area tile, independent of plume."""
    free = np.argwhere(mask == 0)
    points: list[list[int]] = []
    for row in range(5):
        for col in range(6):
            target = np.array(((row + .5) * mask.shape[0] / 5,
                               (col + .5) * mask.shape[1] / 6))
            distances = ((free - target) ** 2).sum(axis=1)
            p = free[int(np.argmin(distances))]
            points.append([int(p[0]), int(p[1])])
    if len({tuple(p) for p in points}) != 30:
        raise ValueError("probe points are not unique")
    return points


def masked_error(prediction: torch.Tensor, target: torch.Tensor,
                 points: list[list[int]]) -> float:
    row = [p[0] for p in points]
    col = [p[1] for p in points]
    p = prediction[:, 0, row, col].clamp_min(0)
    y = target[:, 0, row, col]
    return float(((p - y) ** 2).mean())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_script", type=Path)
    parser.add_argument("bank_root", type=Path)
    parser.add_argument("model_root", type=Path)
    args = parser.parse_args()
    torch.set_num_threads(4)
    module = load_model_module(args.model_script)
    manifest = json.loads((args.model_root / "train_manifest.json").read_text())
    if tuple(manifest["train_cells"]) != module.TRAIN_CELLS:
        raise ValueError("training split drift")
    if tuple(manifest["holdout_cells_unopened"]) != module.HOLDOUT_CELLS:
        raise ValueError("holdout split drift")
    x_s1_w2 = inputs(module, args.bank_root, "S1", "W2")
    x_s2_w2 = inputs(module, args.bank_root, "S2", "W2")
    x_s2_w1 = inputs(module, args.bank_root, "S2", "W1")
    mask = x_s2_w2[0, 4].numpy()
    points = probe_points(mask)
    result = {"probe_grid": "5x6 closest-free equal-area tiles", "points_xy": points,
              "candidate_count": 2, "scores": {}}
    with torch.no_grad():
        for kind, constructor in (("monolithic", module.MonolithicModel),
                                  ("operator", module.OperatorModel)):
            for seed in module.TRAIN_SEEDS:
                key = f"{kind}_seed{seed}"
                checkpoint = args.model_root / f"{key}.pt"
                if sha256(checkpoint) != manifest["fits"][key]["checkpoint_sha256"]:
                    raise ValueError("model hash drift")
                model = constructor()
                model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True))
                model.eval()
                p_s1_w2 = model(x_s1_w2)
                p_s2_w2 = model(x_s2_w2)
                p_s2_w1 = model(x_s2_w1)
                for target_seed in ("A", "B"):
                    target_path = args.bank_root / f"S2_W2_{target_seed}" / "spatial" / "concentration.npy"
                    field = np.load(target_path, allow_pickle=False)
                    if field.shape != (10, 83, 119):
                        raise ValueError("target shape drift")
                    y = F.avg_pool2d(torch.from_numpy(np.log1p(field[:, None])),
                                     2, ceil_mode=True)
                    score_s1 = masked_error(p_s1_w2, y, points)
                    score_s2 = masked_error(p_s2_w2, y, points)
                    wind_swap = masked_error(p_s2_w1, y, points)
                    result["scores"][f"{key}_{target_seed}"] = {
                        "S1_W2_error": score_s1, "S2_W2_error": score_s2,
                        "truth_rank": 1 if score_s2 < score_s1 else 2,
                        "wind_swap_S2_W1_error": wind_swap,
                        "wind_swap_degrades": wind_swap > score_s2,
                    }
    path = args.model_root / "sparse_rank_diagnostic.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["scores"], indent=2))


if __name__ == "__main__":
    main()
